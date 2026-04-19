"""
API Quota and Usage Statistics Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from backend.utils.quota_tracker import quota_tracker, get_quota_summary

router = APIRouter(prefix="/quota", tags=["Quota"])
logger = logging.getLogger(__name__)


@router.get("/")
async def get_all_quota_stats():
    """Get quota statistics for all API providers."""
    try:
        summary = await get_quota_summary()
        return {
            "success": True,
            "data": summary,
        }
    except Exception as e:
        logger.error(f"Failed to get quota stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider}")
async def get_provider_quota_stats(provider: str):
    """Get quota statistics for a specific provider."""
    try:
        summary = await get_quota_summary(provider)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
        
        return {
            "success": True,
            "data": summary,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quota stats for {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/costs")
async def get_cost_summary():
    """Get cost summary across all providers."""
    try:
        all_stats = await get_quota_summary()
        
        total_cost = sum(
            stats.get("total_cost", 0)
            for stats in all_stats.values()
        )
        
        total_calls = sum(
            stats.get("total_calls", 0)
            for stats in all_stats.values()
        )
        
        by_provider = {
            provider: {
                "cost": stats.get("total_cost", 0),
                "calls": stats.get("total_calls", 0),
                "cost_per_call": (
                    stats.get("total_cost", 0) / max(stats.get("total_calls", 1), 1)
                ),
            }
            for provider, stats in all_stats.items()
        }
        
        return {
            "success": True,
            "data": {
                "total_cost": round(total_cost, 4),
                "total_calls": total_calls,
                "average_cost_per_call": round(total_cost / max(total_calls, 1), 6),
                "by_provider": by_provider,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get cost summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/usage")
async def get_usage_summary():
    """Get usage summary across all providers."""
    try:
        all_stats = await get_quota_summary()
        
        total_calls = sum(
            stats.get("total_calls", 0)
            for stats in all_stats.values()
        )
        
        successful_calls = sum(
            stats.get("successful_calls", 0)
            for stats in all_stats.values()
        )
        
        failed_calls = sum(
            stats.get("failed_calls", 0)
            for stats in all_stats.values()
        )
        
        total_tokens = sum(
            stats.get("total_tokens", 0)
            for stats in all_stats.values()
        )
        
        return {
            "success": True,
            "data": {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": round(successful_calls / max(total_calls, 1) * 100, 2),
                "total_tokens": total_tokens,
                "providers_count": len(all_stats),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/daily")
async def reset_daily_stats():
    """Reset daily statistics (admin only)."""
    try:
        await quota_tracker.reset_daily_stats()
        return {
            "success": True,
            "message": "Daily statistics reset successfully",
        }
    except Exception as e:
        logger.error(f"Failed to reset daily stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/monthly")
async def reset_monthly_stats():
    """Reset monthly statistics (admin only)."""
    try:
        await quota_tracker.reset_monthly_stats()
        return {
            "success": True,
            "message": "Monthly statistics reset successfully",
        }
    except Exception as e:
        logger.error(f"Failed to reset monthly stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
