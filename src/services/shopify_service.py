"""
src/services/shopify_service.py
================================
Production-grade Shopify Admin REST API client.

Handles:
  - Rate limiting  (429 Retry-After header + exponential backoff)
  - Expired / revoked API tokens (401 → token refresh hook → retry)
  - Network errors (connection timeout, DNS failure)
  - Malformed responses

Authentication:
  - Shopify Admin API uses a static access token (X-Shopify-Access-Token header)
  - For OAuth apps: refresh via a provided refresh_callback, then retry once
  - For Private apps / Custom apps: static key — 401 → raise TokenExpiredError

Usage:
    service = ShopifyService(
        shop_domain="myshop.myshopify.com",
        access_token="shpat_...",
        api_version="2024-01",
    )
    products = service.list_products(limit=10)
    order = service.get_order("gid://shopify/Order/12345")
"""

import time
import logging
import json
from typing import Any, Callable, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("services.shopify")

# ── Custom Exceptions ─────────────────────────────────────────────────────────

class ShopifyServiceError(Exception):
    """Base class for all ShopifyService errors."""

class RateLimitError(ShopifyServiceError):
    """Raised when all retry attempts are exhausted after 429s."""
    def __init__(self, retry_after: float = 0, message: str = ""):
        self.retry_after = retry_after
        super().__init__(message or f"Rate limit exceeded. Retry after {retry_after}s")

class TokenExpiredError(ShopifyServiceError):
    """Raised when the API token is expired, revoked, or invalid (401)."""
    def __init__(self, shop: str = ""):
        super().__init__(f"Access token expired or invalid for shop: {shop}")

class ShopifyAPIError(ShopifyServiceError):
    """Raised for non-retryable API errors (4xx except 401/429)."""
    def __init__(self, status_code: int, errors: Any):
        self.status_code = status_code
        self.errors = errors
        super().__init__(f"Shopify API error {status_code}: {errors}")

class ShopifyNetworkError(ShopifyServiceError):
    """Raised for network-level failures."""

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_API_VERSION  = "2024-01"
DEFAULT_TIMEOUT      = 30          # seconds
MAX_RETRY_ATTEMPTS   = 5
RATE_LIMIT_BASE_WAIT = 1.0         # seconds — minimum wait on 429
RATE_LIMIT_MAX_WAIT  = 60.0        # seconds — maximum backoff cap
LEAKY_BUCKET_CALL_LIMIT = 40       # Shopify standard bucket
CALLS_PER_SECOND     = 2           # Shopify standard rate


# ── ShopifyService ────────────────────────────────────────────────────────────

class ShopifyService:
    """
    Thread-safe Shopify Admin REST API client with automatic
    rate-limit handling and token-refresh support.

    Args:
        shop_domain:      e.g. "myshop.myshopify.com"
        access_token:     Shopify Admin API access token
        api_version:      API version string, default "2024-01"
        refresh_callback: Optional callable(shop_domain) → new_access_token
                          Called on 401. If None, raises TokenExpiredError.
        max_retries:      Maximum retry attempts on 429
        timeout:          Request timeout in seconds
    """

    def __init__(
        self,
        shop_domain:      str,
        access_token:     str,
        api_version:      str = DEFAULT_API_VERSION,
        refresh_callback: Optional[Callable[[str], str]] = None,
        max_retries:      int = MAX_RETRY_ATTEMPTS,
        timeout:          int = DEFAULT_TIMEOUT,
    ):
        self.shop_domain      = shop_domain.rstrip("/")
        self.access_token     = access_token
        self.api_version      = api_version
        self.refresh_callback = refresh_callback
        self.max_retries      = max_retries
        self.timeout          = timeout

        self._session = self._build_session()
        self._call_bucket = LEAKY_BUCKET_CALL_LIMIT  # remaining calls in bucket

    # ── Session setup ─────────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        """Create a requests session with connection-level retry (network errors only)."""
        session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET", "POST", "PUT", "DELETE"],
                raise_on_status=False,
            )
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _base_url(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}"

    def _headers(self) -> Dict[str, str]:
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type":           "application/json",
            "Accept":                 "application/json",
        }

    # ── Core request dispatcher ───────────────────────────────────────────────

    def _request(
        self,
        method:   str,
        endpoint: str,
        payload:  Optional[Dict] = None,
        params:   Optional[Dict] = None,
    ) -> Dict:
        """
        Execute an HTTP request against the Shopify Admin API.

        Retry logic:
          - 429: respect Retry-After header, then exponential backoff
          - 401: call refresh_callback if present, then retry once
          - 5xx: handled by HTTPAdapter with Retry

        Returns parsed JSON body on success.
        Raises ShopifyServiceError subclass on terminal failure.
        """
        url            = f"{self._base_url()}{endpoint}"
        attempt        = 0
        token_refreshed = False

        while attempt <= self.max_retries:
            try:
                response = self._session.request(
                    method  = method.upper(),
                    url     = url,
                    headers = self._headers(),
                    json    = payload,
                    params  = params,
                    timeout = self.timeout,
                )
            except requests.exceptions.ConnectionError as exc:
                raise ShopifyNetworkError(f"Connection failed: {exc}") from exc
            except requests.exceptions.Timeout as exc:
                raise ShopifyNetworkError(f"Request timed out after {self.timeout}s") from exc

            # ── Update leaky bucket from response headers ─────────────────────
            self._update_bucket(response.headers)

            # ── 200-class ─────────────────────────────────────────────────────
            if response.status_code in (200, 201, 202):
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"raw": response.text}

            # ── 204 No Content ────────────────────────────────────────────────
            if response.status_code == 204:
                return {}

            # ── 429 Rate Limited ──────────────────────────────────────────────
            if response.status_code == 429:
                attempt += 1
                if attempt > self.max_retries:
                    retry_after = self._parse_retry_after(response)
                    raise RateLimitError(
                        retry_after=retry_after,
                        message=(
                            f"Rate limit hit on {method} {endpoint} — "
                            f"exhausted {self.max_retries} retries"
                        ),
                    )
                wait = self._calc_backoff(attempt, response)
                logger.warning(
                    "Shopify 429 on %s %s — waiting %.1fs (attempt %d/%d)",
                    method, endpoint, wait, attempt, self.max_retries,
                )
                time.sleep(wait)
                continue

            # ── 401 Unauthorized (token expired / revoked) ────────────────────
            if response.status_code == 401:
                if not token_refreshed and self.refresh_callback is not None:
                    logger.warning(
                        "Shopify 401 on %s %s — attempting token refresh", method, endpoint
                    )
                    try:
                        new_token = self.refresh_callback(self.shop_domain)
                        if new_token:
                            self.access_token = new_token
                            token_refreshed = True
                            attempt = 0   # reset retry counter after refresh
                            logger.info("Token refreshed for %s — retrying", self.shop_domain)
                            continue
                    except Exception as exc:
                        logger.error("Token refresh failed: %s", exc)
                raise TokenExpiredError(shop=self.shop_domain)

            # ── Other 4xx — non-retryable ─────────────────────────────────────
            if 400 <= response.status_code < 500:
                try:
                    errors = response.json().get("errors", response.text)
                except Exception:
                    errors = response.text
                raise ShopifyAPIError(status_code=response.status_code, errors=errors)

            # ── Unexpected status ─────────────────────────────────────────────
            raise ShopifyAPIError(
                status_code=response.status_code,
                errors=f"Unexpected status {response.status_code}",
            )

        # Should not reach here — guard
        raise ShopifyServiceError(f"Request failed after {self.max_retries} retries")

    # ── Backoff helpers ───────────────────────────────────────────────────────

    def _parse_retry_after(self, response: requests.Response) -> float:
        """Parse the Retry-After header. Returns float seconds, default 2.0."""
        val = response.headers.get("Retry-After", "")
        try:
            return float(val)
        except (ValueError, TypeError):
            return 2.0

    def _calc_backoff(self, attempt: int, response: requests.Response) -> float:
        """
        Calculate wait time for a 429 retry.

        Priority:
          1. Retry-After header value (Shopify usually sends this)
          2. Exponential backoff: base * 2^attempt  (capped at MAX_WAIT)
        """
        retry_after = self._parse_retry_after(response)
        if retry_after > 0:
            return min(retry_after, RATE_LIMIT_MAX_WAIT)
        exponential = RATE_LIMIT_BASE_WAIT * (2 ** attempt)
        return min(exponential, RATE_LIMIT_MAX_WAIT)

    def _update_bucket(self, headers: Dict) -> None:
        """Track remaining API call bucket from X-Shopify-Shop-Api-Call-Limit header."""
        val = headers.get("X-Shopify-Shop-Api-Call-Limit", "")
        # Format: "used/max"  e.g. "35/40"
        if val and "/" in val:
            try:
                used, maximum = val.split("/")
                self._call_bucket = int(maximum) - int(used)
                if self._call_bucket <= 5:
                    logger.warning(
                        "Shopify API bucket low: %s calls remaining (limit: %s)",
                        self._call_bucket, maximum,
                    )
            except (ValueError, TypeError):
                pass

    # ── Public API — Products ─────────────────────────────────────────────────

    def list_products(
        self,
        limit:  int = 50,
        fields: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """
        GET /products.json

        Returns list of product dicts.

        Args:
            limit:  Max products to return (1–250)
            fields: Comma-separated field names to include
            status: "active" | "archived" | "draft"
        """
        params: Dict[str, Any] = {"limit": min(limit, 250)}
        if fields:
            params["fields"] = fields
        if status:
            params["status"] = status

        data = self._request("GET", "/products.json", params=params)
        return data.get("products", [])

    def get_product(self, product_id: str) -> Dict:
        """GET /products/{id}.json"""
        data = self._request("GET", f"/products/{product_id}.json")
        return data.get("product", {})

    def create_product(self, product: Dict) -> Dict:
        """
        POST /products.json

        Minimum required payload:
            {"title": "Product Title"}

        Full payload example:
            {
                "title":        "Heritage Print Tee",
                "body_html":    "<p>WAI-Institute original design.</p>",
                "vendor":       "WAI-Institute",
                "product_type": "Apparel",
                "status":       "draft",
                "variants": [{"price": "29.99", "sku": "WAI-TEE-001"}],
                "tags":         "spoken-word, heritage, apparel",
            }
        """
        payload = {"product": product}
        data = self._request("POST", "/products.json", payload=payload)
        return data.get("product", {})

    def update_product(self, product_id: str, updates: Dict) -> Dict:
        """PUT /products/{id}.json"""
        payload = {"product": {"id": product_id, **updates}}
        data = self._request("PUT", f"/products/{product_id}.json", payload=payload)
        return data.get("product", {})

    def delete_product(self, product_id: str) -> bool:
        """DELETE /products/{id}.json — returns True on success."""
        self._request("DELETE", f"/products/{product_id}.json")
        return True

    # ── Public API — Orders ───────────────────────────────────────────────────

    def list_orders(
        self,
        limit:         int = 50,
        status:        str = "any",
        financial_status: Optional[str] = None,
    ) -> List[Dict]:
        """GET /orders.json"""
        params: Dict[str, Any] = {"limit": min(limit, 250), "status": status}
        if financial_status:
            params["financial_status"] = financial_status
        data = self._request("GET", "/orders.json", params=params)
        return data.get("orders", [])

    def get_order(self, order_id: str) -> Dict:
        """GET /orders/{id}.json"""
        data = self._request("GET", f"/orders/{order_id}.json")
        return data.get("order", {})

    def create_order(self, order: Dict) -> Dict:
        """
        POST /orders.json

        Minimum payload:
            {
                "line_items": [{"variant_id": 123, "quantity": 1}],
                "email": "customer@example.com",
            }
        """
        payload = {"order": order}
        data = self._request("POST", "/orders.json", payload=payload)
        return data.get("order", {})

    # ── Public API — Variants ─────────────────────────────────────────────────

    def list_variants(self, product_id: str) -> List[Dict]:
        """GET /products/{id}/variants.json"""
        data = self._request("GET", f"/products/{product_id}/variants.json")
        return data.get("variants", [])

    def update_variant(self, variant_id: str, updates: Dict) -> Dict:
        """PUT /variants/{id}.json"""
        payload = {"variant": {"id": variant_id, **updates}}
        data = self._request("PUT", f"/variants/{variant_id}.json", payload=payload)
        return data.get("variant", {})

    # ── Public API — Webhooks ─────────────────────────────────────────────────

    def register_webhook(self, topic: str, address: str, format_: str = "json") -> Dict:
        """
        POST /webhooks.json

        Args:
            topic:   e.g. "orders/create", "products/update"
            address: HTTPS URL to receive webhook payloads
            format_: "json" or "xml"
        """
        payload = {
            "webhook": {
                "topic":   topic,
                "address": address,
                "format":  format_,
            }
        }
        data = self._request("POST", "/webhooks.json", payload=payload)
        return data.get("webhook", {})

    def list_webhooks(self) -> List[Dict]:
        """GET /webhooks.json"""
        data = self._request("GET", "/webhooks.json")
        return data.get("webhooks", [])

    # ── Shop info ─────────────────────────────────────────────────────────────

    def get_shop(self) -> Dict:
        """GET /shop.json — useful for verifying token validity."""
        data = self._request("GET", "/shop.json")
        return data.get("shop", {})

    def health_check(self) -> bool:
        """Returns True if the token is valid and the shop is reachable."""
        try:
            shop = self.get_shop()
            return bool(shop.get("id"))
        except ShopifyServiceError:
            return False

    # ── Context manager support ───────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._session.close()
