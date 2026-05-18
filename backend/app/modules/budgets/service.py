import uuid
from decimal import Decimal

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.schemas import BudgetCreate

log = structlog.get_logger()


async def list_budgets(
    db: AsyncSession,
    user_id: uuid.UUID,
    year: int,
    month: int,
    currency: str,
) -> list:
    result = await db.execute(
        text("""
            SELECT
                b.id,
                b.category_id,
                b.amount,
                b.currency,
                b.period_year,
                b.period_month,
                b.alert_pct::numeric / 100  AS alert_threshold,
                COALESCE(SUM(
                    CASE WHEN e.direction = 'credit'
                         AND NOT t.is_transfer
                    THEN e.amount ELSE 0 END
                ), 0) AS spent
            FROM budgets b
            LEFT JOIN categories c ON c.id = b.category_id
            LEFT JOIN transactions t
                ON  t.category_id = b.category_id
                AND t.user_id     = b.user_id
                AND t.currency    = b.currency
                AND t.deleted_at  IS NULL
                AND t.status      = 'confirmed'
                AND EXTRACT(YEAR  FROM t.occurred_at) = b.period_year
                AND EXTRACT(MONTH FROM t.occurred_at) = b.period_month
            LEFT JOIN entries e ON e.transaction_id = t.id
            WHERE b.user_id     = :uid
              AND b.period_year  = :year
              AND b.period_month = :month
              AND b.currency     = :currency
            GROUP BY b.id, b.category_id, b.amount, b.currency,
                     b.period_year, b.period_month, b.alert_pct
            ORDER BY c.name
        """),
        {
            "uid": str(user_id),
            "year": year,
            "month": month,
            "currency": currency,
        },
    )
    rows = result.mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        spent = d["spent"]
        d["remaining"] = d["amount"] - spent
        out.append(d)
    return out


async def create_budget(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: BudgetCreate,
) -> dict:
    alert_pct = int(data.alert_threshold * 100)
    result = await db.execute(
        text("""
            INSERT INTO budgets
                (user_id, module, category_id, currency, amount,
                 period_year, period_month, alert_pct)
            SELECT
                :uid,
                c.module,
                :category_id,
                :currency,
                :amount,
                :year,
                :month,
                :alert_pct
            FROM categories c
            WHERE c.id = :category_id AND c.user_id = :uid
            ON CONFLICT (user_id, category_id, period_year, period_month)
            DO UPDATE SET
                amount    = EXCLUDED.amount,
                alert_pct = EXCLUDED.alert_pct
            RETURNING id, category_id, amount, currency,
                      period_year, period_month,
                      alert_pct::numeric / 100 AS alert_threshold
        """),
        {
            "uid": str(user_id),
            "category_id": str(data.category_id),
            "currency": data.currency,
            "amount": data.amount,
            "year": data.period_year,
            "month": data.period_month,
            "alert_pct": alert_pct,
        },
    )
    await db.commit()
    row = dict(result.mappings().one())
    row["spent"] = Decimal("0")
    row["remaining"] = row["amount"]
    log.info("budget_upserted", budget_id=str(row["id"]), user_id=str(user_id))
    return row


async def delete_budget(
    db: AsyncSession,
    user_id: uuid.UUID,
    budget_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        text("DELETE FROM budgets WHERE id = :id AND user_id = :uid RETURNING id"),
        {"id": str(budget_id), "uid": str(user_id)},
    )
    await db.commit()
    return result.rowcount > 0  # type: ignore[attr-defined]
