"""
src/tests/test_shopify_service.py
====================================
Full mocked test suite for ShopifyService.

Tests cover:
  - Successful API calls and correct JSON payload structure
  - 429 rate limit: Retry-After header respected, retries occur, final RateLimitError
  - 401 token expired: raises TokenExpiredError without refresh_callback
  - 401 token refresh: refresh_callback called, token updated, request retried successfully
  - 403 / 4xx non-retryable errors: ShopifyAPIError raised immediately
  - Network errors: ShopifyNetworkError raised on ConnectionError and Timeout
  - Bucket tracking from X-Shopify-Shop-Api-Call-Limit header
  - Product CRUD payload structure validation
  - Order create payload structure validation
  - Webhook registration payload structure validation
  - Health check returns True/False correctly

Run:
    python -m pytest src/tests/test_shopify_service.py -v
    # or
    python -m unittest src.tests.test_shopify_service -v
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.services.shopify_service import (
    ShopifyService,
    RateLimitError,
    TokenExpiredError,
    ShopifyAPIError,
    ShopifyNetworkError,
)

import requests as _requests


# ── Test helpers ──────────────────────────────────────────────────────────────

def make_response(status_code=200, json_body=None, headers=None, content=None):
    """Build a mock requests.Response."""
    resp                = MagicMock(spec=_requests.Response)
    resp.status_code    = status_code
    resp.headers        = headers or {}
    if json_body is not None:
        resp.json.return_value = json_body
    if content is not None:
        resp.content = content
    resp.text = str(json_body or "")
    return resp


SHOP_DOMAIN    = "testshop.myshopify.com"
ACCESS_TOKEN   = "shpat_test_token_abc123"
BASE_URL       = f"https://{SHOP_DOMAIN}/admin/api/2024-01"

STANDARD_HEADERS = {"X-Shopify-Shop-Api-Call-Limit": "10/40"}


# ══════════════════════════════════════════════════════════════════════════════
# Helper: build service with patched session
# ══════════════════════════════════════════════════════════════════════════════

def make_service(**kwargs):
    with patch("src.services.shopify_service.HTTPAdapter"), \
         patch("src.services.shopify_service.Retry"):
        svc = ShopifyService(
            shop_domain=SHOP_DOMAIN,
            access_token=ACCESS_TOKEN,
            **kwargs,
        )
    return svc


# ══════════════════════════════════════════════════════════════════════════════
# 1. Product listing
# ══════════════════════════════════════════════════════════════════════════════

class TestListProducts(unittest.TestCase):

    def test_returns_products_list(self):
        """list_products returns the 'products' array from the response."""
        svc = make_service()
        products_data = [
            {"id": 1, "title": "Heritage Tee"},
            {"id": 2, "title": "Spoken Word Poster"},
        ]
        mock_resp = make_response(200, {"products": products_data}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp):
            result = svc.list_products(limit=10)

        self.assertEqual(result, products_data)
        self.assertEqual(len(result), 2)

    def test_limit_capped_at_250(self):
        """limit parameter is capped at 250 regardless of what caller passes."""
        svc = make_service()
        mock_resp = make_response(200, {"products": []}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            svc.list_products(limit=500)
            _, kwargs = mock_req.call_args
            self.assertLessEqual(kwargs["params"]["limit"], 250)

    def test_request_headers_contain_access_token(self):
        """Every request must include X-Shopify-Access-Token header."""
        svc = make_service()
        mock_resp = make_response(200, {"products": []}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            svc.list_products()
            _, kwargs = mock_req.call_args
            self.assertEqual(kwargs["headers"]["X-Shopify-Access-Token"], ACCESS_TOKEN)

    def test_correct_endpoint_called(self):
        """list_products calls /products.json endpoint."""
        svc = make_service()
        mock_resp = make_response(200, {"products": []}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            svc.list_products()
            _, kwargs = mock_req.call_args
            self.assertIn("/products.json", kwargs["url"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. Product creation — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateProduct(unittest.TestCase):

    def test_payload_wrapped_in_product_key(self):
        """create_product must wrap the dict in {'product': ...} before POSTing."""
        svc = make_service()
        created = {"id": 99, "title": "Heritage Print Tee", "status": "draft"}
        mock_resp = make_response(201, {"product": created}, STANDARD_HEADERS)

        product_input = {
            "title":        "Heritage Print Tee",
            "body_html":    "<p>WAI-Institute original.</p>",
            "vendor":       "WAI-Institute",
            "product_type": "Apparel",
            "status":       "draft",
            "variants":     [{"price": "29.99", "sku": "WAI-TEE-001"}],
        }

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            result = svc.create_product(product_input)

        # Verify wrapping
        _, kwargs = mock_req.call_args
        self.assertIn("product", kwargs["json"])
        self.assertEqual(kwargs["json"]["product"]["title"], "Heritage Print Tee")
        self.assertEqual(kwargs["json"]["product"]["status"], "draft")

        # Verify return value is the product (unwrapped)
        self.assertEqual(result["id"], 99)
        self.assertEqual(result["title"], "Heritage Print Tee")

    def test_create_uses_post_method(self):
        """create_product must use POST, not GET or PUT."""
        svc = make_service()
        mock_resp = make_response(201, {"product": {"id": 1}}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            svc.create_product({"title": "Test"})
            _, kwargs = mock_req.call_args
            self.assertEqual(kwargs["method"], "POST")

    def test_returns_empty_dict_on_missing_product_key(self):
        """If response has no 'product' key, return empty dict — don't crash."""
        svc = make_service()
        mock_resp = make_response(201, {}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp):
            result = svc.create_product({"title": "Ghost Product"})
        self.assertEqual(result, {})


# ══════════════════════════════════════════════════════════════════════════════
# 3. Order creation — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateOrder(unittest.TestCase):

    def test_order_payload_structure(self):
        """create_order wraps order dict in {'order': ...}."""
        svc = make_service()
        order_input = {
            "line_items": [{"variant_id": 123, "quantity": 1}],
            "email":      "customer@example.com",
            "financial_status": "paid",
        }
        returned_order = {"id": 555, **order_input}
        mock_resp = make_response(201, {"order": returned_order}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            result = svc.create_order(order_input)

        _, kwargs = mock_req.call_args
        self.assertIn("order", kwargs["json"])
        self.assertEqual(kwargs["json"]["order"]["email"], "customer@example.com")
        self.assertEqual(kwargs["json"]["order"]["line_items"][0]["variant_id"], 123)
        self.assertEqual(result["id"], 555)

    def test_order_uses_post_method(self):
        svc = make_service()
        mock_resp = make_response(201, {"order": {"id": 1}}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            svc.create_order({"line_items": []})
            _, kwargs = mock_req.call_args
            self.assertEqual(kwargs["method"], "POST")


# ══════════════════════════════════════════════════════════════════════════════
# 4. Webhook registration — payload structure
# ══════════════════════════════════════════════════════════════════════════════

class TestWebhookRegistration(unittest.TestCase):

    def test_webhook_payload_structure(self):
        """register_webhook sends correct topic/address/format payload."""
        svc = make_service()
        hook = {"id": 1, "topic": "orders/create", "address": "https://example.com/hook"}
        mock_resp = make_response(201, {"webhook": hook}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp) as mock_req:
            result = svc.register_webhook(
                topic="orders/create",
                address="https://example.com/hook",
            )

        _, kwargs = mock_req.call_args
        wh = kwargs["json"]["webhook"]
        self.assertEqual(wh["topic"],   "orders/create")
        self.assertEqual(wh["address"], "https://example.com/hook")
        self.assertEqual(wh["format"],  "json")
        self.assertEqual(result["topic"], "orders/create")


# ══════════════════════════════════════════════════════════════════════════════
# 5. Rate limit handling (429)
# ══════════════════════════════════════════════════════════════════════════════

class TestRateLimitHandling(unittest.TestCase):

    @patch("src.services.shopify_service.time.sleep")
    def test_retries_on_429_then_succeeds(self, mock_sleep):
        """On 429, service waits and retries — succeeds on second attempt."""
        svc = make_service(max_retries=3)

        rate_limit_resp = make_response(
            429, None, {"Retry-After": "2.5", **STANDARD_HEADERS}
        )
        success_resp = make_response(200, {"products": [{"id": 1}]}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", side_effect=[rate_limit_resp, success_resp]):
            result = svc.list_products()

        self.assertEqual(result, [{"id": 1}])
        mock_sleep.assert_called_once_with(2.5)

    @patch("src.services.shopify_service.time.sleep")
    def test_raises_rate_limit_error_after_max_retries(self, mock_sleep):
        """After max_retries 429 responses, raises RateLimitError."""
        svc = make_service(max_retries=2)

        rate_limit_resp = make_response(
            429, None, {"Retry-After": "1.0", **STANDARD_HEADERS}
        )

        with patch.object(svc._session, "request", return_value=rate_limit_resp):
            with self.assertRaises(RateLimitError) as ctx:
                svc.list_products()

        self.assertEqual(ctx.exception.retry_after, 1.0)
        self.assertEqual(mock_sleep.call_count, 2)  # max_retries = 2

    @patch("src.services.shopify_service.time.sleep")
    def test_uses_exponential_backoff_when_no_retry_after(self, mock_sleep):
        """Falls back to exponential backoff if Retry-After header is absent."""
        svc = make_service(max_retries=2)
        rate_limit_resp = make_response(429, None, {**STANDARD_HEADERS})  # No Retry-After
        success_resp    = make_response(200, {"products": []}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", side_effect=[rate_limit_resp, success_resp]):
            svc.list_products()

        wait_time = mock_sleep.call_args[0][0]
        self.assertGreater(wait_time, 0)
        self.assertLessEqual(wait_time, 60.0)

    @patch("src.services.shopify_service.time.sleep")
    def test_retry_after_capped_at_max_wait(self, mock_sleep):
        """Retry-After value greater than MAX_WAIT is capped."""
        from src.services.shopify_service import RATE_LIMIT_MAX_WAIT
        svc = make_service(max_retries=2)
        resp_429 = make_response(429, None, {"Retry-After": "9999", **STANDARD_HEADERS})
        resp_200 = make_response(200, {"products": []}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", side_effect=[resp_429, resp_200]):
            svc.list_products()

        wait_time = mock_sleep.call_args[0][0]
        self.assertLessEqual(wait_time, RATE_LIMIT_MAX_WAIT)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Token expiry handling (401)
# ══════════════════════════════════════════════════════════════════════════════

class TestTokenExpiryHandling(unittest.TestCase):

    def test_raises_token_expired_without_callback(self):
        """401 without refresh_callback → raises TokenExpiredError immediately."""
        svc = make_service()
        mock_resp = make_response(401, {"errors": "Invalid API key"}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", return_value=mock_resp):
            with self.assertRaises(TokenExpiredError) as ctx:
                svc.list_products()

        self.assertIn(SHOP_DOMAIN, str(ctx.exception))

    def test_refresh_callback_called_on_401(self):
        """401 triggers refresh_callback, new token set, request retried."""
        new_token = "shpat_refreshed_token_xyz"
        refresh_cb = MagicMock(return_value=new_token)

        svc = make_service(refresh_callback=refresh_cb)

        resp_401     = make_response(401, {}, STANDARD_HEADERS)
        resp_success = make_response(200, {"products": [{"id": 42}]}, STANDARD_HEADERS)

        with patch.object(svc._session, "request", side_effect=[resp_401, resp_success]):
            result = svc.list_products()

        refresh_cb.assert_called_once_with(SHOP_DOMAIN)
        self.assertEqual(svc.access_token, new_token)
        self.assertEqual(result, [{"id": 42}])

    def test_raises_token_expired_if_callback_returns_none(self):
        """If refresh_callback returns None/falsy, raises TokenExpiredError."""
        refresh_cb = MagicMock(return_value=None)
        svc = make_service(refresh_callback=refresh_cb)

        resp_401 = make_response(401, {}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=resp_401):
            with self.assertRaises(TokenExpiredError):
                svc.list_products()

    def test_no_infinite_loop_after_refresh(self):
        """After refresh, if 401 recurs — raises TokenExpiredError (no infinite loop)."""
        new_token  = "shpat_still_bad_token"
        refresh_cb = MagicMock(return_value=new_token)
        svc        = make_service(refresh_callback=refresh_cb)

        resp_401 = make_response(401, {}, STANDARD_HEADERS)
        # Both calls return 401 — should raise after second 401
        with patch.object(svc._session, "request", return_value=resp_401):
            with self.assertRaises(TokenExpiredError):
                svc.list_products()

        # Callback called exactly once (no retry loop)
        refresh_cb.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# 7. Non-retryable 4xx errors
# ══════════════════════════════════════════════════════════════════════════════

class TestNonRetryableErrors(unittest.TestCase):

    def test_404_raises_shopify_api_error(self):
        svc = make_service()
        mock_resp = make_response(404, {"errors": "Not Found"}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp):
            with self.assertRaises(ShopifyAPIError) as ctx:
                svc.get_product("999999")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_422_raises_shopify_api_error(self):
        svc = make_service()
        mock_resp = make_response(
            422,
            {"errors": {"title": ["can't be blank"]}},
            STANDARD_HEADERS,
        )
        with patch.object(svc._session, "request", return_value=mock_resp):
            with self.assertRaises(ShopifyAPIError) as ctx:
                svc.create_product({})
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("title", str(ctx.exception.errors))

    def test_403_raises_shopify_api_error(self):
        svc = make_service()
        mock_resp = make_response(403, {"errors": "Forbidden"}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp):
            with self.assertRaises(ShopifyAPIError) as ctx:
                svc.list_products()
        self.assertEqual(ctx.exception.status_code, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 8. Network errors
# ══════════════════════════════════════════════════════════════════════════════

class TestNetworkErrors(unittest.TestCase):

    def test_connection_error_raises_network_error(self):
        svc = make_service()
        with patch.object(
            svc._session, "request",
            side_effect=_requests.exceptions.ConnectionError("DNS failure")
        ):
            with self.assertRaises(ShopifyNetworkError) as ctx:
                svc.list_products()
        self.assertIn("Connection failed", str(ctx.exception))

    def test_timeout_raises_network_error(self):
        svc = make_service(timeout=5)
        with patch.object(
            svc._session, "request",
            side_effect=_requests.exceptions.Timeout("timed out")
        ):
            with self.assertRaises(ShopifyNetworkError) as ctx:
                svc.list_products()
        self.assertIn("timed out", str(ctx.exception))


# ══════════════════════════════════════════════════════════════════════════════
# 9. Call bucket tracking
# ══════════════════════════════════════════════════════════════════════════════

class TestBucketTracking(unittest.TestCase):

    def test_bucket_updated_from_header(self):
        """_call_bucket should reflect remaining calls from response header."""
        svc = make_service()
        mock_resp = make_response(
            200,
            {"products": []},
            {"X-Shopify-Shop-Api-Call-Limit": "35/40"},
        )
        with patch.object(svc._session, "request", return_value=mock_resp):
            svc.list_products()
        self.assertEqual(svc._call_bucket, 5)   # 40 - 35 = 5

    def test_bucket_not_updated_on_missing_header(self):
        """Missing bucket header should not crash — bucket keeps prior value."""
        svc = make_service()
        svc._call_bucket = 20  # set a known starting value

        mock_resp = make_response(200, {"products": []}, {})  # no bucket header
        with patch.object(svc._session, "request", return_value=mock_resp):
            svc.list_products()
        self.assertEqual(svc._call_bucket, 20)  # unchanged


# ══════════════════════════════════════════════════════════════════════════════
# 10. Health check
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthCheck(unittest.TestCase):

    def test_health_check_true_when_shop_returned(self):
        svc = make_service()
        mock_resp = make_response(
            200,
            {"shop": {"id": 12345, "name": "testshop"}},
            STANDARD_HEADERS,
        )
        with patch.object(svc._session, "request", return_value=mock_resp):
            self.assertTrue(svc.health_check())

    def test_health_check_false_on_401(self):
        svc = make_service()
        mock_resp = make_response(401, {}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp):
            self.assertFalse(svc.health_check())

    def test_health_check_false_on_network_error(self):
        svc = make_service()
        with patch.object(
            svc._session, "request",
            side_effect=_requests.exceptions.ConnectionError("down")
        ):
            self.assertFalse(svc.health_check())

    def test_health_check_false_when_shop_has_no_id(self):
        svc = make_service()
        mock_resp = make_response(200, {"shop": {}}, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp):
            self.assertFalse(svc.health_check())


# ══════════════════════════════════════════════════════════════════════════════
# 11. 204 No Content
# ══════════════════════════════════════════════════════════════════════════════

class TestNoContent(unittest.TestCase):

    def test_delete_returns_true_on_204(self):
        svc = make_service()
        mock_resp = make_response(204, None, STANDARD_HEADERS)
        with patch.object(svc._session, "request", return_value=mock_resp):
            result = svc.delete_product("12345")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
