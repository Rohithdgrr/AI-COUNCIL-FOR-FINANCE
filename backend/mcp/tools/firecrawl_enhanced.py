"""
Enhanced Firecrawl Tools with Advanced Features

Features:
- Request deduplication (coalescing)
- Adaptive rate limiting
- Smart content extraction pipeline
- Parallel multi-format scraping
- Relevance scoring
- Incremental crawling
- Comprehensive metrics
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import httpx
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Request Deduplication Layer
# ============================================================================

class FirecrawlDeduplicationLayer:
    """Prevent redundant scrapes using in-flight request tracking."""
    
    def __init__(self):
        self._in_flight: Dict[str, asyncio.Future] = {}
        self._completed_results: Dict[str, Tuple[dict, datetime]] = {}
        self._lock = asyncio.Lock()
        self._result_ttl = 30  # seconds
    
    def _generate_key(self, url: str, formats: List[str]) -> str:
        """Generate cache key from URL and formats."""
        formats_str = ",".join(sorted(formats))
        return hashlib.md5(f"{url}:{formats_str}".encode()).hexdigest()
    
    async def deduped_scrape(self, url: str, formats: List[str], scrape_fn) -> dict:
        """Execute scrape with deduplication."""
        cache_key = self._generate_key(url, formats)
        
        async with self._lock:
            # Check if request is already in-flight
            if cache_key in self._in_flight:
                logger.info(f"🔄 Joining in-flight scrape for {url}")
                # Wait for existing request
                future = self._in_flight[cache_key]
        
        # If we found an in-flight request, wait for it
        if cache_key in self._in_flight:
            try:
                return await self._in_flight[cache_key]
            except Exception as e:
                logger.warning(f"In-flight request failed: {e}")
                # Fall through to make new request
        
        async with self._lock:
            # Check recent completed results
            if cache_key in self._completed_results:
                result, timestamp = self._completed_results[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._result_ttl):
                    logger.info(f"✅ Using recent scrape result for {url}")
                    return result
            
            # Create new request
            future = asyncio.Future()
            self._in_flight[cache_key] = future
        
        try:
            # Execute scrape
            result = await scrape_fn()
            
            # Store result
            async with self._lock:
                self._completed_results[cache_key] = (result, datetime.now())
                future.set_result(result)
                del self._in_flight[cache_key]
            
            # Cleanup old results
            await self._cleanup_old_results()
            
            return result
        except Exception as e:
            async with self._lock:
                future.set_exception(e)
                del self._in_flight[cache_key]
            raise
    
    async def _cleanup_old_results(self):
        """Remove results older than TTL."""
        now = datetime.now()
        to_remove = [
            key for key, (_, timestamp) in self._completed_results.items()
            if now - timestamp > timedelta(seconds=self._result_ttl * 2)
        ]
        for key in to_remove:
            del self._completed_results[key]
    
    def get_stats(self) -> dict:
        """Get deduplication statistics."""
        return {
            "inflight_requests": len(self._in_flight),
            "cached_results": len(self._completed_results),
            "cache_ttl_seconds": self._result_ttl,
        }


# ============================================================================
# Adaptive Rate Limiter
# ============================================================================

class AdaptiveRateLimiter:
    """Token bucket rate limiter with dynamic adjustment based on server health."""
    
    def __init__(self, initial_rate: float = 10.0):
        self.tokens = initial_rate
        self.max_tokens = initial_rate
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
        # Server health tracking
        self.success_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0
        self.request_count = 0
        self.adaptive_rate = initial_rate
        
        # Metrics
        self.requests_per_minute = 0.0
        self.last_minute_count = 0
        self.last_minute_reset = time.monotonic()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            
            # Add tokens based on adaptive rate
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.adaptive_rate
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.adaptive_rate
                logger.debug(f"⏳ Rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            
            self.tokens -= 1
            
            # Update requests per minute
            if now - self.last_minute_reset >= 60:
                self.requests_per_minute = self.last_minute_count
                self.last_minute_count = 0
                self.last_minute_reset = now
            self.last_minute_count += 1
    
    def record_result(self, success: bool, response_time: float):
        """Record request result and adjust rate."""
        self.request_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        self.total_response_time += response_time
        
        # Calculate metrics
        success_rate = self.success_count / max(self.request_count, 1)
        avg_response_time = self.total_response_time / max(self.request_count, 1)
        
        # Adaptive adjustment
        if self.request_count % 10 == 0:  # Adjust every 10 requests
            if success_rate > 0.95 and avg_response_time < 2.0:
                # Increase rate if healthy
                old_rate = self.adaptive_rate
                self.adaptive_rate = min(50, self.adaptive_rate * 1.1)
                if old_rate != self.adaptive_rate:
                    logger.info(
                        f"📈 Firecrawl rate increased to {self.adaptive_rate:.1f} req/s "
                        f"(success={success_rate:.2%}, avg_time={avg_response_time:.2f}s)"
                    )
            elif success_rate < 0.8 or avg_response_time > 5.0:
                # Decrease rate if struggling
                old_rate = self.adaptive_rate
                self.adaptive_rate = max(1, self.adaptive_rate * 0.7)
                if old_rate != self.adaptive_rate:
                    logger.warning(
                        f"📉 Firecrawl rate decreased to {self.adaptive_rate:.1f} req/s "
                        f"(success={success_rate:.2%}, avg_time={avg_response_time:.2f}s)"
                    )
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        success_rate = self.success_count / max(self.request_count, 1)
        avg_response_time = self.total_response_time / max(self.request_count, 1)
        
        return {
            "adaptive_rate": round(self.adaptive_rate, 2),
            "current_tokens": round(self.tokens, 2),
            "max_tokens": self.max_tokens,
            "success_rate": round(success_rate, 4),
            "avg_response_time": round(avg_response_time, 2),
            "total_requests": self.request_count,
            "requests_per_minute": self.requests_per_minute,
        }


# ============================================================================
# Smart Content Extraction Pipeline
# ============================================================================

class SmartContentExtractor:
    """Multi-stage extraction with progressive fallback."""
    
    async def extract(
        self,
        url: str,
        schema: Optional[dict] = None,
        extract_prompt: Optional[str] = None,
        scrape_fn = None,
        extract_fn = None,
    ) -> dict:
        """
        Extraction pipeline:
        1. Try LLM-based extraction (if available)
        2. Try rule-based extraction (CSS selectors, regex)
        3. Return raw markdown as fallback
        """
        # Stage 1: LLM extraction
        if (schema or extract_prompt) and extract_fn:
            try:
                result = await extract_fn(url, schema, extract_prompt)
                if not result.get("fallback"):
                    return {
                        "method": "llm_extract",
                        "data": result.get("data", {}),
                        "confidence": 0.9,
                        "url": url,
                    }
            except Exception as e:
                logger.info(f"LLM extraction failed for {url}: {e}")
        
        # Stage 2: Rule-based extraction
        if scrape_fn:
            try:
                scrape_result = await scrape_fn(url, ["markdown", "html"])
                html = scrape_result.get("data", {}).get("html", "")
                markdown = scrape_result.get("data", {}).get("markdown", "")
                
                # Extract common patterns
                extracted = self._rule_based_extract(html, markdown, schema)
                if extracted:
                    return {
                        "method": "rule_based",
                        "data": extracted,
                        "confidence": 0.7,
                        "url": url,
                    }
            except Exception as e:
                logger.info(f"Rule-based extraction failed for {url}: {e}")
        
        # Stage 3: Raw content fallback
        try:
            scrape_result = await scrape_fn(url, ["markdown"])
            markdown = scrape_result.get("data", {}).get("markdown", "")
            return {
                "method": "raw_scrape",
                "data": {"raw_content": markdown},
                "confidence": 0.5,
                "url": url,
            }
        except Exception as e:
            return {
                "method": "failed",
                "data": {},
                "confidence": 0.0,
                "url": url,
                "error": str(e),
            }
    
    def _rule_based_extract(
        self,
        html: str,
        markdown: str,
        schema: Optional[dict]
    ) -> Optional[dict]:
        """Extract data using regex patterns and heuristics."""
        if not html and not markdown:
            return None
        
        result = {}
        
        # Common extraction patterns
        patterns = {
            "company_name": [
                r'(?i)<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']',
                r'(?i)<title>([^<|]+)',
                r'©\s*(\d{4})?\s*([^<\n]+?)\s*(Inc|LLC|Ltd|Corp|Corporation)',
            ],
            "email": [
                r'[\w\.-]+@[\w\.-]+\.\w+',
            ],
            "phone": [
                r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}',
                r'\+\d{1,3}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}',
            ],
            "certifications": [
                r'\b(ISO\s*\d{4,5}|IATF\s*16949|AS\d+|FDA|CE\s*Mark|UL|CSA)\b',
            ],
            "address": [
                r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir)[,\s]+[\w\s]+,\s*[A-Z]{2}\s+\d{5}',
            ],
        }
        
        # Extract based on schema fields
        if schema and "properties" in schema:
            for field in schema["properties"].keys():
                field_patterns = patterns.get(field, [])
                for pattern in field_patterns:
                    match = re.search(pattern, html + "\n" + markdown, re.IGNORECASE)
                    if match:
                        result[field] = match.group(1) if match.groups() else match.group(0)
                        break
        else:
            # Extract all common fields
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    matches = re.findall(pattern, html + "\n" + markdown, re.IGNORECASE)
                    if matches:
                        if field in ["certifications"]:
                            result[field] = list(set(matches))
                        else:
                            result[field] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        break
        
        return result if result else None


# ============================================================================
# Parallel Multi-Format Scraping
# ============================================================================

async def scrape_parallel_formats(
    url: str,
    formats: List[str],
    scrape_fn
) -> dict:
    """Scrape URL with multiple formats in parallel, merging results."""
    # Remove duplicates while preserving order
    unique_formats = list(dict.fromkeys(formats))
    
    # For single format, use direct request
    if len(unique_formats) == 1:
        return await scrape_fn(url, [unique_formats[0]])
    
    # For multiple formats, fetch in parallel and merge
    async def fetch_format(fmt: str) -> dict:
        try:
            result = await scrape_fn(url, [fmt])
            return {"format": fmt, "data": result.get("data", {})}
        except Exception as e:
            logger.warning(f"Failed to fetch {fmt} for {url}: {e}")
            return {"format": fmt, "error": str(e)}
    
    # Execute parallel requests
    results = await asyncio.gather(*[fetch_format(f) for f in unique_formats])
    
    # Merge results
    merged = {"data": {"metadata": {}}}
    for r in results:
        if "error" not in r:
            fmt = r["format"]
            data = r["data"]
            
            # Merge content
            if fmt in ["markdown", "html", "rawHtml"]:
                merged["data"][fmt] = data.get(fmt, "")
            elif fmt == "extract":
                merged["data"]["extract"] = data.get("extract", {})
            
            # Merge metadata (take first non-empty)
            if not merged["data"]["metadata"]:
                merged["data"]["metadata"] = data.get("metadata", {})
    
    return merged


# ============================================================================
# Firecrawl Metrics Tracker
# ============================================================================

class FirecrawlMetrics:
    """Track Firecrawl performance metrics."""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.cache_hits = 0
        self.total_response_time = 0.0
        self.total_content_size = 0
        self.requests_by_endpoint = defaultdict(int)
        self.errors_by_type = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_request(
        self,
        endpoint: str,
        success: bool,
        response_time: float,
        content_size: int = 0,
        cached: bool = False,
        error_type: Optional[str] = None,
    ):
        """Record request metrics."""
        self.request_count += 1
        self.requests_by_endpoint[endpoint] += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error_type:
                self.errors_by_type[error_type] += 1
        
        if cached:
            self.cache_hits += 1
        
        self.total_response_time += response_time
        self.total_content_size += content_size
    
    def get_summary(self) -> dict:
        """Get metrics summary."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_count / max(self.request_count, 1), 4),
            "cache_hits": self.cache_hits,
            "cache_hit_rate": round(self.cache_hits / max(self.request_count, 1), 4),
            "avg_response_time": round(self.total_response_time / max(self.request_count, 1), 2),
            "total_content_mb": round(self.total_content_size / 1024 / 1024, 2),
            "requests_per_minute": round(self.request_count / max(uptime / 60, 1), 2),
            "requests_by_endpoint": dict(self.requests_by_endpoint),
            "errors_by_type": dict(self.errors_by_type),
        }


# ============================================================================
# Global Instances
# ============================================================================

deduplication_layer = FirecrawlDeduplicationLayer()
rate_limiter = AdaptiveRateLimiter(initial_rate=10.0)
content_extractor = SmartContentExtractor()
metrics_tracker = FirecrawlMetrics()


# ============================================================================
# Enhanced API Functions
# ============================================================================

async def enhanced_scrape(
    url: str,
    formats: List[str],
    base_scrape_fn,
    use_dedup: bool = True,
    use_rate_limit: bool = True,
) -> dict:
    """Enhanced scrape with deduplication and rate limiting."""
    start_time = time.monotonic()
    
    try:
        # Apply rate limiting
        if use_rate_limit:
            await rate_limiter.acquire()
        
        # Apply deduplication
        if use_dedup:
            result = await deduplication_layer.deduped_scrape(
                url,
                formats,
                lambda: base_scrape_fn(url, formats)
            )
        else:
            result = await base_scrape_fn(url, formats)
        
        # Record metrics
        response_time = time.monotonic() - start_time
        content_size = len(str(result))
        rate_limiter.record_result(True, response_time)
        metrics_tracker.record_request(
            "scrape",
            True,
            response_time,
            content_size,
            cached=use_dedup,
        )
        
        return result
    
    except Exception as e:
        response_time = time.monotonic() - start_time
        rate_limiter.record_result(False, response_time)
        metrics_tracker.record_request(
            "scrape",
            False,
            response_time,
            error_type=type(e).__name__,
        )
        raise


def get_enhanced_stats() -> dict:
    """Get all enhancement statistics."""
    return {
        "deduplication": deduplication_layer.get_stats(),
        "rate_limiter": rate_limiter.get_stats(),
        "metrics": metrics_tracker.get_summary(),
    }
