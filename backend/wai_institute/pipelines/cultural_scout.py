"""
WAI-Institute Cultural Scout
=============================
Autonomous social media and trend scanner for the spoken-word pipeline.

Scans:
  Reddit      — r/poetry, r/spokenword, r/blackpoetry, r/WritingPrompts, etc.
                (free public JSON API — no auth needed)
  RSS/Trends  — Google Trends RSS + curated poetry/culture RSS feeds
  YouTube     — YouTube Data API v3 comments on spoken word videos
                (requires YOUTUBE_API_KEY — optional, degrades gracefully)
  Twitter/X   — Basic API v2 search (requires TWITTER_BEARER_TOKEN — optional)

Each lead is scored for emotional resonance and intent before storing.
Leads persist to db.scout_leads for the ContextualMatcher to process.

Usage:
    scout = CulturalScout(db)
    leads = await scout.run_full_scan()   # all platforms
    leads = await scout.scan_reddit()     # single platform
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

logger = logging.getLogger("lcewai.cultural_scout")

# ── Config ────────────────────────────────────────────────────────────────────

YOUTUBE_API_KEY     = os.environ.get("YOUTUBE_API_KEY", "")
TWITTER_BEARER      = os.environ.get("TWITTER_BEARER_TOKEN", "")
ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")

# Reddit subreddits to scan
REDDIT_SUBREDDITS = [
    "poetry",
    "spokenword",
    "BlackPoetry",
    "WritingPrompts",
    "blacklit",
    "afropoetry",
    "OCPoetry",
]

# RSS feeds for cultural/trend signals
RSS_FEEDS = [
    "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
    "https://www.poetryfoundation.org/feeds/poems.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",
]

# YouTube spoken word video IDs to scan for comments
YOUTUBE_VIDEO_SEEDS = [
    # Placeholder IDs — replace with actual spoken word videos you own/track
    # "VIDEO_ID_1",
]

# Emotional intent keywords that indicate a high-value lead
HIGH_INTENT_KEYWORDS = [
    "looking for", "anyone know", "does anyone have", "need something",
    "recommend", "help me find", "searching for", "where can i find",
    "poetry about", "spoken word about", "poem for", "healing poem",
    "something for grief", "missing someone", "need to hear",
    "struggling with", "going through", "dealing with",
    "anyone else feel", "this hits", "this is exactly",
]

# Emotional themes that match our catalog
EMOTIONAL_THEMES = [
    "grief", "loss", "healing", "love", "identity", "blackness",
    "resilience", "struggle", "hope", "community", "ancestry",
    "trauma", "joy", "rage", "justice", "freedom",
    "relationships", "loneliness", "purpose", "growth",
]

# HTTP headers for Reddit (must include User-Agent)
REDDIT_HEADERS = {
    "User-Agent": "WAI-Institute-Scout/1.0 (cultural intelligence bot)",
    "Accept":     "application/json",
}


class CulturalScout:
    """
    Autonomous cultural intelligence scanner.
    Runs as a background task on the configured schedule.
    """

    def __init__(self, db=None):
        self.db = db

    # ── Full Scan ─────────────────────────────────────────────────────────────

    async def run_full_scan(self, max_leads_per_source: int = 20) -> dict:
        """
        Run all platform scanners. Returns combined lead count.
        Safe to call repeatedly — deduplicates by source_id.
        """
        scan_id = str(uuid.uuid4())
        started = datetime.now(timezone.utc)
        logger.info("CulturalScout: starting full scan %s", scan_id)

        results = await asyncio.gather(
            self.scan_reddit(limit=max_leads_per_source),
            self.scan_rss(limit=max_leads_per_source),
            self.scan_youtube(limit=max_leads_per_source),
            self.scan_twitter(limit=max_leads_per_source),
            return_exceptions=True,
        )

        reddit_leads  = results[0] if not isinstance(results[0], Exception) else []
        rss_leads     = results[1] if not isinstance(results[1], Exception) else []
        youtube_leads = results[2] if not isinstance(results[2], Exception) else []
        twitter_leads = results[3] if not isinstance(results[3], Exception) else []

        all_leads = reddit_leads + rss_leads + youtube_leads + twitter_leads
        stored    = await self._store_leads(all_leads, scan_id)

        duration = (datetime.now(timezone.utc) - started).total_seconds()
        summary = {
            "scan_id":       scan_id,
            "started_at":    started.isoformat(),
            "duration_secs": round(duration, 2),
            "leads_found": {
                "reddit":   len(reddit_leads),
                "rss":      len(rss_leads),
                "youtube":  len(youtube_leads),
                "twitter":  len(twitter_leads),
                "total":    len(all_leads),
            },
            "leads_stored":  stored,
        }

        # Log scan to DB
        if self.db is not None:
            try:
                await self.db.scout_scan_log.insert_one({
                    "_id":    scan_id,
                    **summary,
                })
            except Exception: pass

        logger.info("CulturalScout: scan complete — %d leads found, %d stored", len(all_leads), stored)
        return summary

    # ── Reddit ────────────────────────────────────────────────────────────────

    async def scan_reddit(self, limit: int = 20) -> list:
        """
        Scan configured subreddits for high-intent posts.
        Uses Reddit's free public JSON API — no auth required.
        Returns list of raw lead dicts.
        """
        leads = []
        async with httpx.AsyncClient(
            headers=REDDIT_HEADERS, timeout=15, follow_redirects=True
        ) as client:
            for subreddit in REDDIT_SUBREDDITS:
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
                    r = await client.get(url)
                    if r.status_code != 200:
                        logger.warning("Reddit r/%s: HTTP %d", subreddit, r.status_code)
                        continue

                    data = r.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        p = post.get("data", {})
                        title = p.get("title", "")
                        body  = p.get("selftext", "")
                        text  = f"{title} {body}".lower()

                        score, theme, intent = self._score_content(text)
                        if score < 1:
                            continue

                        leads.append({
                            "source":     "reddit",
                            "subreddit":  subreddit,
                            "source_id":  f"reddit_{p.get('id', '')}",
                            "title":      title,
                            "body":       body[:500],
                            "url":        f"https://reddit.com{p.get('permalink', '')}",
                            "author":     p.get("author", ""),
                            "score":      score,
                            "theme":      theme,
                            "intent":     intent,
                            "upvotes":    p.get("score", 0),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

                        if len(leads) >= limit:
                            return leads

                except Exception as e:
                    logger.warning("Reddit scan r/%s error: %s", subreddit, e)

        return leads

    # ── RSS / Google Trends ───────────────────────────────────────────────────

    async def scan_rss(self, limit: int = 20) -> list:
        """
        Scan RSS feeds for cultural signals and trending topics.
        Parses XML without feedparser dependency (uses stdlib xml.etree).
        """
        import xml.etree.ElementTree as ET
        leads = []

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for feed_url in RSS_FEEDS:
                try:
                    r = await client.get(
                        feed_url,
                        headers={"User-Agent": "WAI-Institute-Scout/1.0"},
                    )
                    if r.status_code != 200:
                        continue

                    try:
                        root = ET.fromstring(r.text)
                    except ET.ParseError:
                        continue

                    # Handle both RSS and Atom formats
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    items = (
                        root.findall(".//item") or
                        root.findall(".//atom:entry", ns)
                    )

                    for item in items[:15]:
                        title_el = item.find("title")
                        desc_el  = item.find("description") or item.find("summary")
                        link_el  = item.find("link")

                        title = title_el.text if title_el is not None else ""
                        desc  = desc_el.text  if desc_el  is not None else ""
                        link  = link_el.text  if link_el  is not None else ""

                        text = f"{title} {desc}".lower()
                        score, theme, intent = self._score_content(text)

                        # RSS: include anything with a relevant theme (lower bar)
                        if score < 1 and not any(t in text for t in EMOTIONAL_THEMES):
                            continue

                        leads.append({
                            "source":     "rss",
                            "feed_url":   feed_url,
                            "source_id":  f"rss_{uuid.uuid5(uuid.NAMESPACE_URL, feed_url + title)}",
                            "title":      title[:200],
                            "body":       desc[:500] if desc else "",
                            "url":        link,
                            "score":      max(score, 1),
                            "theme":      theme or "cultural_trend",
                            "intent":     intent,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

                        if len(leads) >= limit:
                            return leads

                except Exception as e:
                    logger.warning("RSS scan %s error: %s", feed_url, e)

        return leads

    # ── YouTube ───────────────────────────────────────────────────────────────

    async def scan_youtube(self, limit: int = 20) -> list:
        """
        Scan YouTube comments on spoken word videos for audience intent.
        Requires YOUTUBE_API_KEY. Degrades gracefully without it.
        """
        if not YOUTUBE_API_KEY:
            logger.info("CulturalScout: YOUTUBE_API_KEY not set — skipping YouTube scan")
            return []

        leads = []
        async with httpx.AsyncClient(timeout=15) as client:
            # First: search for trending spoken word videos
            try:
                search_url = "https://www.googleapis.com/youtube/v3/search"
                search_params = {
                    "key":        YOUTUBE_API_KEY,
                    "q":          "spoken word poetry Black excellence",
                    "type":       "video",
                    "order":      "viewCount",
                    "maxResults": 5,
                    "part":       "snippet",
                }
                r = await client.get(search_url, params=search_params)
                if r.status_code != 200:
                    logger.warning("YouTube search failed: HTTP %d", r.status_code)
                    return []

                video_ids = [
                    item["id"]["videoId"]
                    for item in r.json().get("items", [])
                ]
            except Exception as e:
                logger.warning("YouTube search error: %s", e)
                return []

            # Then: scan top comments on those videos
            for video_id in video_ids[:3]:
                try:
                    comments_url = "https://www.googleapis.com/youtube/v3/commentThreads"
                    r = await client.get(comments_url, params={
                        "key":        YOUTUBE_API_KEY,
                        "videoId":    video_id,
                        "maxResults": 20,
                        "order":      "relevance",
                        "part":       "snippet",
                    })
                    if r.status_code != 200:
                        continue

                    for item in r.json().get("items", []):
                        comment = item["snippet"]["topLevelComment"]["snippet"]
                        text = comment.get("textDisplay", "").lower()
                        score, theme, intent = self._score_content(text)

                        if score < 2:  # Higher bar for YouTube comments
                            continue

                        leads.append({
                            "source":     "youtube",
                            "video_id":   video_id,
                            "source_id":  f"yt_{item.get('id', '')}",
                            "body":       text[:400],
                            "url":        f"https://youtube.com/watch?v={video_id}",
                            "score":      score,
                            "theme":      theme,
                            "intent":     intent,
                            "likes":      comment.get("likeCount", 0),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

                        if len(leads) >= limit:
                            return leads

                except Exception as e:
                    logger.warning("YouTube comments error (video %s): %s", video_id, e)

        return leads

    # ── Twitter/X ─────────────────────────────────────────────────────────────

    async def scan_twitter(self, limit: int = 10) -> list:
        """
        Scan Twitter/X for spoken word / poetry intent.
        Requires TWITTER_BEARER_TOKEN. Free tier = 500 posts/month.
        Degrades gracefully without the token.
        """
        if not TWITTER_BEARER:
            logger.info("CulturalScout: TWITTER_BEARER_TOKEN not set — skipping Twitter scan")
            return []

        leads = []
        queries = [
            "spoken word poetry -is:retweet lang:en",
            "poetry healing grief -is:retweet lang:en",
            "Black poetry powerful -is:retweet lang:en",
        ]

        headers = {
            "Authorization": f"Bearer {TWITTER_BEARER}",
            "User-Agent":    "WAI-Institute-Scout/1.0",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            for query in queries[:1]:  # Conservative — preserve free tier quota
                try:
                    r = await client.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        params={
                            "query":        query,
                            "max_results":  10,
                            "tweet.fields": "text,created_at,author_id,public_metrics",
                        },
                        headers=headers,
                    )
                    if r.status_code == 429:
                        logger.warning("Twitter rate limit reached")
                        break
                    if r.status_code != 200:
                        logger.warning("Twitter scan failed: HTTP %d — %s", r.status_code, r.text[:100])
                        continue

                    for tweet in r.json().get("data", []):
                        text = tweet.get("text", "").lower()
                        score, theme, intent = self._score_content(text)

                        if score < 1:
                            continue

                        leads.append({
                            "source":    "twitter",
                            "source_id": f"tw_{tweet.get('id', '')}",
                            "body":      tweet.get("text", "")[:280],
                            "score":     score,
                            "theme":     theme,
                            "intent":    intent,
                            "metrics":   tweet.get("public_metrics", {}),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })

                        if len(leads) >= limit:
                            break

                except Exception as e:
                    logger.warning("Twitter scan error: %s", e)

        return leads

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score_content(self, text: str) -> tuple[int, str, str]:
        """
        Score a piece of text for lead quality.

        Returns:
            score (int):  0-5 (0=noise, 5=hot lead)
            theme (str):  primary emotional theme detected
            intent (str): "seeking" | "sharing" | "trending" | "none"
        """
        text = text.lower()
        score = 0
        theme = ""
        intent = "none"

        # Intent keywords (high value — someone is actively seeking)
        seeking_count = sum(1 for kw in HIGH_INTENT_KEYWORDS if kw in text)
        if seeking_count > 0:
            score += seeking_count * 2
            intent = "seeking"

        # Emotional theme match
        for t in EMOTIONAL_THEMES:
            if t in text:
                score += 1
                if not theme:
                    theme = t

        # Engagement signals
        if any(w in text for w in ["need", "looking", "anyone", "help", "find me"]):
            score += 1
            if intent == "none":
                intent = "seeking"

        if any(w in text for w in ["this hits", "crying", "felt this", "needed this", "sharing"]):
            score += 1
            intent = "sharing"

        return min(score, 5), theme, intent

    # ── Storage ───────────────────────────────────────────────────────────────

    async def _store_leads(self, leads: list, scan_id: str) -> int:
        """
        Store leads in db.scout_leads.
        Deduplicates by source_id. Returns count of newly stored leads.
        """
        if self.db is None or not leads:
            return 0

        stored = 0
        for lead in leads:
            source_id = lead.get("source_id")
            if not source_id:
                continue
            try:
                # Check for duplicate
                existing = await self.db.scout_leads.find_one({"source_id": source_id})
                if existing:
                    continue

                lead["_id"]     = str(uuid.uuid4())
                lead["scan_id"] = scan_id
                lead["matched"] = False  # ContextualMatcher hasn't run yet
                lead["actioned"] = False

                await self.db.scout_leads.insert_one(lead)
                stored += 1
            except Exception as e:
                logger.warning("_store_leads error for %s: %s", source_id, e)

        return stored

    # ── Retrieval ─────────────────────────────────────────────────────────────

    async def get_unmatched_leads(self, limit: int = 50) -> list:
        """Return leads that haven't been processed by the ContextualMatcher yet."""
        leads = []
        if self.db is None:
            return leads
        try:
            cursor = self.db.scout_leads.find(
                {"matched": False},
                {"_id": 0},
            ).sort("score", -1).limit(limit)
            async for doc in cursor:
                leads.append(doc)
        except Exception as e:
            logger.warning("get_unmatched_leads error: %s", e)
        return leads

    async def get_hot_leads(self, min_score: int = 3, limit: int = 20) -> list:
        """Return high-score leads (score >= min_score)."""
        leads = []
        if self.db is None:
            return leads
        try:
            cursor = self.db.scout_leads.find(
                {"score": {"$gte": min_score}, "actioned": False},
                {"_id": 0},
            ).sort("score", -1).limit(limit)
            async for doc in cursor:
                leads.append(doc)
        except Exception as e:
            logger.warning("get_hot_leads error: %s", e)
        return leads
