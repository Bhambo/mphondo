"""Arq task definitions.

Tasks:
  - parse_mpesa_pdf   : background PDF parsing (heavy OCR fallback)
  - refresh_fx_rates  : daily EUR/MZN rate fetch and cache
  - send_push         : ntfy.sh push notification
  - check_budgets     : alert when spending exceeds threshold
"""

import uuid

import httpx
import structlog
from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.core.config import settings
from app.core.currency import get_fx_rate

log = structlog.get_logger()


async def parse_mpesa_pdf(ctx: dict, statement_id: str, file_bytes: bytes) -> dict:
    """Parse an M-Pesa PDF statement in the background."""
    from app.core.database import AsyncSessionLocal
    from app.modules.mpesa.parser import parse_pdf
    from app.modules.mpesa.service import _store_parsed_ops  # internal

    log.info("worker_parse_mpesa_pdf", statement_id=statement_id)
    ops = parse_pdf(file_bytes)

    async with AsyncSessionLocal() as db:
        await _store_parsed_ops(db, uuid.UUID(statement_id), ops)

    return {"statement_id": statement_id, "count": len(ops)}


async def refresh_fx_rates(ctx: dict) -> dict:
    """Fetch EUR/MZN and store in fx_rates table + Redis cache."""
    redis: Redis = ctx["redis"]

    try:
        rate = await get_fx_rate(redis, base="EUR", target="MZN")
        log.info("worker_fx_refreshed", eur_mzn=str(rate))

        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO fx_rates (from_currency, to_currency, rate, rate_date, source)
                    VALUES ('EUR', 'MZN', :rate, CURRENT_DATE, 'exchangerate.host')
                    ON CONFLICT (from_currency, to_currency, rate_date) DO NOTHING
                """),
                {"rate": rate},
            )
            await db.commit()

        return {"eur_mzn": str(rate)}
    except Exception as exc:
        log.error("worker_fx_failed", error=str(exc))
        raise


async def send_push(ctx: dict, topic: str, title: str, message: str) -> None:
    """Send a push notification via ntfy.sh."""
    if not settings.NTFY_TOPIC:
        return

    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(
            f"{settings.NTFY_URL}/{topic}",
            content=message,
            headers={"Title": title, "Priority": "default"},
        )
    log.info("worker_push_sent", topic=topic)


async def check_budgets(ctx: dict, user_id: str) -> dict:
    """Check if any budget has exceeded its alert threshold and push notification."""
    from sqlalchemy import text

    from app.core.database import AsyncSessionLocal

    alerts_sent = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT b.id, b.amount, b.alert_pct, b.currency,
                       c.name as category_name,
                       COALESCE(SUM(
                         CASE WHEN e.direction = 'debit' THEN e.amount ELSE 0 END
                       ), 0) as spent
                FROM budgets b
                JOIN categories c ON c.id = b.category_id
                LEFT JOIN transactions t ON
                    t.category_id = b.category_id
                    AND EXTRACT(YEAR FROM t.occurred_at) = b.period_year
                    AND EXTRACT(MONTH FROM t.occurred_at) = b.period_month
                    AND t.user_id = :uid AND t.deleted_at IS NULL
                LEFT JOIN entries e ON e.transaction_id = t.id
                WHERE b.user_id = :uid
                GROUP BY b.id, b.amount, b.alert_pct, b.currency, c.name
                HAVING COALESCE(SUM(
                    CASE WHEN e.direction = 'debit' THEN e.amount ELSE 0 END
                ), 0) >= b.amount * (b.alert_pct::numeric / 100)
            """),
            {"uid": user_id},
        )
        rows = result.mappings().all()

    for row in rows:
        pct = int((row["spent"] / row["amount"]) * 100)
        await send_push(
            ctx,
            topic=settings.NTFY_TOPIC,
            title=f"Presupuesto: {row['category_name']}",
            message=f"Alerta {row['alert_pct']}% — Has gastado {pct}% ({row['currency']})",
        )
        alerts_sent += 1

    return {"alerts_sent": alerts_sent}


class WorkerSettings:
    functions = [parse_mpesa_pdf, refresh_fx_rates, send_push, check_budgets]

    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
    )

    # Cron jobs
    cron_jobs = [
        # Refresh FX rates every 4 hours
        {
            "coroutine": refresh_fx_rates,
            "hour": {0, 4, 8, 12, 16, 20},
            "minute": 15,
        },
    ]

    max_jobs = 10
    job_timeout = 300  # 5 min max per job
    keep_result = 3600
