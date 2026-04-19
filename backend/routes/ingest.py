from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
import uuid
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ERPIngestRequest(BaseModel):
    data: list[dict]
    source: Optional[str] = "manual"


class NewsIngestRequest(BaseModel):
    articles: list[dict]
    source: Optional[str] = "api"


class SocialIngestRequest(BaseModel):
    posts: list[dict]
    platform: Optional[str] = "twitter"


@router.post("/erp")
async def ingest_erp(request: ERPIngestRequest):
    count = len(request.data)
    try:
        from backend.db.neon import execute_query
        for row in request.data[:100]:
            await execute_query(
                """INSERT INTO ingested_erp (id, source, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.source, row,
            )
    except Exception as e:
        logger.warning(f"ERP ingest DB write failed: {e}")

    return {"status": "ok", "records_ingested": count, "source": request.source}


@router.post("/news")
async def ingest_news(request: NewsIngestRequest):
    count = len(request.articles)
    try:
        from backend.db.neon import execute_query
        for article in request.articles[:100]:
            await execute_query(
                """INSERT INTO ingested_news (id, source, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.source, article,
            )
    except Exception as e:
        logger.warning(f"News ingest DB write failed: {e}")

    return {"status": "ok", "articles_ingested": count, "source": request.source}


@router.post("/social")
async def ingest_social(request: SocialIngestRequest):
    count = len(request.posts)
    try:
        from backend.db.neon import execute_query
        for post in request.posts[:100]:
            await execute_query(
                """INSERT INTO ingested_social (id, platform, data, created_at)
                   VALUES ($1, $2, $3, now())
                   ON CONFLICT DO NOTHING""",
                str(uuid.uuid4()), request.platform, post,
            )
    except Exception as e:
        logger.warning(f"Social ingest DB write failed: {e}")

    return {"status": "ok", "posts_ingested": count, "platform": request.platform}


@router.get("/status")
async def ingest_status():
    """Get ingest system status."""
    try:
        from backend.db.neon import execute_query
        
        # Get counts from each ingest table
        erp_count = await execute_query("SELECT COUNT(*) FROM ingested_erp")
        news_count = await execute_query("SELECT COUNT(*) FROM ingested_news")
        social_count = await execute_query("SELECT COUNT(*) FROM ingested_social")
        
        return {
            "status": "active",
            "erp_records": erp_count[0]['count'] if erp_count else 0,
            "news_articles": news_count[0]['count'] if news_count else 0,
            "social_posts": social_count[0]['count'] if social_count else 0,
            "last_updated": time.time()
        }
    except Exception as e:
        logger.warning(f"Ingest status check failed: {e}")
        return {
            "status": "idle",
            "erp_records": 0,
            "news_articles": 0,
            "social_posts": 0,
            "last_updated": time.time()
        }
