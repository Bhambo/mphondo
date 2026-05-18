"""FX rate helpers — fetch, cache in Redis, and return Decimal snapshots."""

import decimal
from datetime import date

import httpx
import structlog
from redis.asyncio import Redis

from app.core.config import settings

log = structlog.get_logger()

_CACHE_TTL = 60 * 60 * 4  # 4 hours
_FREE_ENDPOINT = "https://open.er-api.com/v6/latest/{base}"
_PAID_ENDPOINT = (
    "https://api.exchangerate.host/live?access_key={key}&source={base}&currencies={targets}"
)


async def get_fx_rate(
    redis: Redis,
    base: str,
    target: str,
    reference_date: date | None = None,
) -> decimal.Decimal:
    """Return the exchange rate base→target, cached in Redis."""
    cache_key = f"fx:{base}:{target}:{reference_date or 'live'}"

    cached = await redis.get(cache_key)
    if cached:
        return decimal.Decimal(cached.decode())

    rate = await _fetch_rate(base, target)
    await redis.setex(cache_key, _CACHE_TTL, str(rate))
    return rate


async def _fetch_rate(base: str, target: str) -> decimal.Decimal:
    async with httpx.AsyncClient(timeout=10) as client:
        if settings.FX_API_KEY:
            url = _PAID_ENDPOINT.format(key=settings.FX_API_KEY, base=base, targets=target)
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            rate = data["quotes"][f"{base}{target}"]
        else:
            url = _FREE_ENDPOINT.format(base=base)
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            rate = data["rates"][target]

    log.info("fx_fetched", base=base, target=target, rate=rate)
    return decimal.Decimal(str(rate))
