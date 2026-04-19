"""
API Quota and Cost Tracking System

Features:
- Track API usage per provider
- Monitor quota limits
- Calculate costs
- Alert on quota exhaustion
- Usage analytics
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class QuotaConfig:
    """Configuration for API quota limits."""
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    cost_per_call: float = 0.0
    cost_per_1k_tokens: float = 0.0
    rate_limit_per_minute: Optional[int] = None


@dataclass
class UsageStats:
    """Usage statistics for an API."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_call: Optional[datetime] = None
    daily_calls: Dict[str, int] = field(default_factory=dict)
    monthly_calls: Dict[str, int] = field(default_factory=dict)


# Quota configurations for different API providers
QUOTA_CONFIGS = {
    "alpha_vantage": QuotaConfig(
        daily_limit=500,
        monthly_limit=None,
        cost_per_call=0.0,  # Free tier
        rate_limit_per_minute=5,
    ),
    "polygon": QuotaConfig(
        daily_limit=None,
        monthly_limit=100000,
        cost_per_call=0.0001,
        rate_limit_per_minute=100,
    ),
    "finnhub": QuotaConfig(
        daily_limit=None,
        monthly_limit=60000,
        cost_per_call=0.0,  # Free tier
        rate_limit_per_minute=60,
    ),
    "openai": QuotaConfig(
        daily_limit=None,
        monthly_limit=None,
        cost_per_1k_tokens=0.002,  # GPT-4o-mini
        rate_limit_per_minute=500,
    ),
    "anthropic": QuotaConfig(
        daily_limit=None,
        monthly_limit=None,
        cost_per_1k_tokens=0.003,  # Claude Haiku
        rate_limit_per_minute=1000,
    ),
    "groq": QuotaConfig(
        daily_limit=14400,
        monthly_limit=None,
        cost_per_call=0.0,  # Free tier
        rate_limit_per_minute=30,
    ),
    "nvidia": QuotaConfig(
        daily_limit=None,
        monthly_limit=None,
        cost_per_call=0.0,  # Free tier
        rate_limit_per_minute=100,
    ),
    "cerebras": QuotaConfig(
        daily_limit=None,
        monthly_limit=None,
        cost_per_call=0.0,  # Free tier
        rate_limit_per_minute=100,
    ),
}


class QuotaTracker:
    """Track API usage and enforce quota limits."""
    
    def __init__(self):
        self.usage_stats: Dict[str, UsageStats] = {}
        self.quota_configs = QUOTA_CONFIGS
    
    def _get_stats(self, provider: str) -> UsageStats:
        """Get or create usage stats for a provider."""
        if provider not in self.usage_stats:
            self.usage_stats[provider] = UsageStats()
        return self.usage_stats[provider]
    
    def _get_date_key(self, date_type: str = "daily") -> str:
        """Get date key for tracking."""
        now = datetime.now()
        if date_type == "daily":
            return now.strftime("%Y-%m-%d")
        elif date_type == "monthly":
            return now.strftime("%Y-%m")
        return now.isoformat()
    
    async def record_call(
        self,
        provider: str,
        success: bool = True,
        tokens: int = 0,
        cost: Optional[float] = None,
    ):
        """Record an API call."""
        stats = self._get_stats(provider)
        config = self.quota_configs.get(provider, QuotaConfig())
        
        # Update counters
        stats.total_calls += 1
        if success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
        
        stats.total_tokens += tokens
        stats.last_call = datetime.now()
        
        # Update daily/monthly counters
        daily_key = self._get_date_key("daily")
        monthly_key = self._get_date_key("monthly")
        
        stats.daily_calls[daily_key] = stats.daily_calls.get(daily_key, 0) + 1
        stats.monthly_calls[monthly_key] = stats.monthly_calls.get(monthly_key, 0) + 1
        
        # Calculate cost
        if cost is not None:
            stats.total_cost += cost
        elif config.cost_per_call > 0:
            stats.total_cost += config.cost_per_call
        elif config.cost_per_1k_tokens > 0 and tokens > 0:
            stats.total_cost += (tokens / 1000) * config.cost_per_1k_tokens
        
        # Check quota limits
        await self._check_quota_limits(provider, stats, config)
        
        # Persist to Redis
        await self._persist_stats(provider, stats)
    
    async def _check_quota_limits(
        self,
        provider: str,
        stats: UsageStats,
        config: QuotaConfig,
    ):
        """Check if quota limits are exceeded."""
        daily_key = self._get_date_key("daily")
        monthly_key = self._get_date_key("monthly")
        
        daily_usage = stats.daily_calls.get(daily_key, 0)
        monthly_usage = stats.monthly_calls.get(monthly_key, 0)
        
        # Check daily limit
        if config.daily_limit and daily_usage >= config.daily_limit:
            logger.warning(
                f"⚠️ {provider} daily quota exceeded: {daily_usage}/{config.daily_limit}"
            )
        elif config.daily_limit and daily_usage >= config.daily_limit * 0.8:
            logger.info(
                f"📊 {provider} approaching daily quota: {daily_usage}/{config.daily_limit}"
            )
        
        # Check monthly limit
        if config.monthly_limit and monthly_usage >= config.monthly_limit:
            logger.warning(
                f"⚠️ {provider} monthly quota exceeded: {monthly_usage}/{config.monthly_limit}"
            )
        elif config.monthly_limit and monthly_usage >= config.monthly_limit * 0.8:
            logger.info(
                f"📊 {provider} approaching monthly quota: {monthly_usage}/{config.monthly_limit}"
            )
    
    async def _persist_stats(self, provider: str, stats: UsageStats):
        """Persist usage stats to Redis."""
        try:
            from backend.db.redis_client import get_redis
            r = await get_redis()
            if r is None:
                return
            
            key = f"quota:{provider}"
            data = {
                "total_calls": stats.total_calls,
                "successful_calls": stats.successful_calls,
                "failed_calls": stats.failed_calls,
                "total_tokens": stats.total_tokens,
                "total_cost": stats.total_cost,
                "last_call": stats.last_call.isoformat() if stats.last_call else None,
                "daily_calls": stats.daily_calls,
                "monthly_calls": stats.monthly_calls,
            }
            
            await r.setex(key, 86400 * 31, json.dumps(data))  # 31 days TTL
        except Exception as e:
            logger.warning(f"Failed to persist quota stats: {e}")
    
    async def _load_stats(self, provider: str) -> Optional[UsageStats]:
        """Load usage stats from Redis."""
        try:
            from backend.db.redis_client import get_redis
            r = await get_redis()
            if r is None:
                return None
            
            key = f"quota:{provider}"
            data = await r.get(key)
            if not data:
                return None
            
            parsed = json.loads(data)
            return UsageStats(
                total_calls=parsed.get("total_calls", 0),
                successful_calls=parsed.get("successful_calls", 0),
                failed_calls=parsed.get("failed_calls", 0),
                total_tokens=parsed.get("total_tokens", 0),
                total_cost=parsed.get("total_cost", 0.0),
                last_call=datetime.fromisoformat(parsed["last_call"]) if parsed.get("last_call") else None,
                daily_calls=parsed.get("daily_calls", {}),
                monthly_calls=parsed.get("monthly_calls", {}),
            )
        except Exception as e:
            logger.warning(f"Failed to load quota stats: {e}")
            return None
    
    async def get_usage_summary(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get usage summary for one or all providers."""
        if provider:
            # Load from Redis if not in memory
            if provider not in self.usage_stats:
                loaded = await self._load_stats(provider)
                if loaded:
                    self.usage_stats[provider] = loaded
            
            stats = self._get_stats(provider)
            config = self.quota_configs.get(provider, QuotaConfig())
            
            daily_key = self._get_date_key("daily")
            monthly_key = self._get_date_key("monthly")
            
            return {
                "provider": provider,
                "total_calls": stats.total_calls,
                "successful_calls": stats.successful_calls,
                "failed_calls": stats.failed_calls,
                "success_rate": (
                    stats.successful_calls / max(stats.total_calls, 1) * 100
                ),
                "total_tokens": stats.total_tokens,
                "total_cost": round(stats.total_cost, 4),
                "daily_usage": stats.daily_calls.get(daily_key, 0),
                "daily_limit": config.daily_limit,
                "daily_remaining": (
                    config.daily_limit - stats.daily_calls.get(daily_key, 0)
                    if config.daily_limit else None
                ),
                "monthly_usage": stats.monthly_calls.get(monthly_key, 0),
                "monthly_limit": config.monthly_limit,
                "monthly_remaining": (
                    config.monthly_limit - stats.monthly_calls.get(monthly_key, 0)
                    if config.monthly_limit else None
                ),
                "last_call": stats.last_call.isoformat() if stats.last_call else None,
            }
        else:
            # Return summary for all providers
            summaries = {}
            for prov in self.quota_configs.keys():
                summaries[prov] = await self.get_usage_summary(prov)
            return summaries
    
    async def reset_daily_stats(self):
        """Reset daily statistics (called by scheduler)."""
        daily_key = self._get_date_key("daily")
        for stats in self.usage_stats.values():
            # Keep only today's stats
            stats.daily_calls = {daily_key: stats.daily_calls.get(daily_key, 0)}
    
    async def reset_monthly_stats(self):
        """Reset monthly statistics (called by scheduler)."""
        monthly_key = self._get_date_key("monthly")
        for stats in self.usage_stats.values():
            # Keep only this month's stats
            stats.monthly_calls = {monthly_key: stats.monthly_calls.get(monthly_key, 0)}


# Global quota tracker instance
quota_tracker = QuotaTracker()


# Convenience functions
async def record_api_call(
    provider: str,
    success: bool = True,
    tokens: int = 0,
    cost: Optional[float] = None,
):
    """Record an API call."""
    await quota_tracker.record_call(provider, success, tokens, cost)


async def get_quota_summary(provider: Optional[str] = None) -> Dict[str, Any]:
    """Get quota usage summary."""
    return await quota_tracker.get_usage_summary(provider)


# Example usage:
"""
from backend.utils.quota_tracker import record_api_call, get_quota_summary

# Record API call
await record_api_call("alpha_vantage", success=True)
await record_api_call("openai", success=True, tokens=1500)

# Get usage summary
summary = await get_quota_summary("alpha_vantage")
print(f"Daily usage: {summary['daily_usage']}/{summary['daily_limit']}")
print(f"Total cost: ${summary['total_cost']}")

# Get all providers
all_summaries = await get_quota_summary()
"""
