"""Ledger service — double-entry transaction CRUD.

The PostgreSQL trigger `trg_double_entry` enforces balance=0 at DB level.
The Pydantic validator in TransactionCreate does the same client-side to
give a friendlier error before hitting the DB.
"""

import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ledger.schemas import TransactionCreate

log = structlog.get_logger()


async def create_transaction(db: AsyncSession, user_id: uuid.UUID, data: TransactionCreate) -> dict:
    async with db.begin():
        result = await db.execute(
            text("""
                INSERT INTO transactions
                    (user_id, module, currency, description, occurred_at,
                     category_id, contact_id, fx_rate_id, fx_rate_snapshot,
                     reference, notes)
                VALUES
                    (:uid, :module, :currency, :description, :occurred_at::timestamptz,
                     :category_id, :contact_id, :fx_rate_id, :fx_rate_snapshot,
                     :reference, :notes)
                RETURNING *
            """),
            {
                "uid": str(user_id),
                "module": data.module,
                "currency": data.currency,
                "description": data.description,
                "occurred_at": data.occurred_at,
                "category_id": str(data.category_id) if data.category_id else None,
                "contact_id": str(data.contact_id) if data.contact_id else None,
                "fx_rate_id": str(data.fx_rate_id) if data.fx_rate_id else None,
                "fx_rate_snapshot": data.fx_rate_snapshot,
                "reference": data.reference,
                "notes": data.notes,
            },
        )
        tx = result.mappings().one()
        tx_id = tx["id"]

        for entry in data.entries:
            await db.execute(
                text("""
                    INSERT INTO entries (transaction_id, account_id, direction, amount, notes)
                    VALUES (:tx_id, :account_id, :direction, :amount, :notes)
                """),
                {
                    "tx_id": str(tx_id),
                    "account_id": str(entry.account_id),
                    "direction": entry.direction,
                    "amount": entry.amount,
                    "notes": entry.notes,
                },
            )

    log.info("transaction_created", tx_id=str(tx_id), user_id=str(user_id))
    tx_out = await get_transaction(db, user_id, tx_id)
    assert tx_out is not None
    return tx_out


async def get_transaction(db: AsyncSession, user_id: uuid.UUID, tx_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        text("SELECT * FROM transactions WHERE id = :id AND user_id = :uid AND deleted_at IS NULL"),
        {"id": str(tx_id), "uid": str(user_id)},
    )
    tx = result.mappings().one_or_none()
    if tx is None:
        return None

    entries_result = await db.execute(
        text("SELECT * FROM entries WHERE transaction_id = :tx_id"),
        {"tx_id": str(tx_id)},
    )
    return {**dict(tx), "entries": entries_result.mappings().all()}


async def list_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    module: str | None,
    account_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    from_date: str | None,
    to_date: str | None,
    limit: int,
    offset: int,
) -> list:
    conditions = ["t.user_id = :uid", "t.deleted_at IS NULL"]
    params: dict = {"uid": str(user_id), "limit": limit, "offset": offset}

    if module:
        conditions.append("t.module = :module")
        params["module"] = module

    if account_id:
        conditions.append(
            "EXISTS ("
            "SELECT 1 FROM entries e "
            "WHERE e.transaction_id = t.id AND e.account_id = :account_id)"
        )
        params["account_id"] = str(account_id)

    if category_id:
        conditions.append("t.category_id = :category_id")
        params["category_id"] = str(category_id)

    if from_date:
        conditions.append("t.occurred_at >= :from_date::timestamptz")
        params["from_date"] = from_date

    if to_date:
        conditions.append("t.occurred_at <= :to_date::timestamptz")
        params["to_date"] = to_date

    where = " AND ".join(conditions)
    order = "ORDER BY t.occurred_at DESC LIMIT :limit OFFSET :offset"
    query = f"SELECT t.* FROM transactions t WHERE {where} {order}"  # noqa: S608
    result = await db.execute(text(query), params)
    txs = list(result.mappings().all())

    if not txs:
        return []

    id_params = {f"id{i}": str(t["id"]) for i, t in enumerate(txs)}
    placeholders = ", ".join(f":id{i}" for i in range(len(txs)))
    entries_result = await db.execute(
        text(f"SELECT * FROM entries WHERE transaction_id IN ({placeholders})"),  # noqa: S608
        id_params,
    )
    entries_by_tx: dict[str, list] = {}
    for e in entries_result.mappings().all():
        entries_by_tx.setdefault(str(e["transaction_id"]), []).append(dict(e))

    return [{**dict(t), "entries": entries_by_tx.get(str(t["id"]), [])} for t in txs]


async def soft_delete_transaction(db: AsyncSession, user_id: uuid.UUID, tx_id: uuid.UUID) -> bool:
    result = await db.execute(
        text("""
            UPDATE transactions
            SET deleted_at = NOW()
            WHERE id = :id AND user_id = :uid AND deleted_at IS NULL
            RETURNING id
        """),
        {"id": str(tx_id), "uid": str(user_id)},
    )
    await db.commit()
    return result.rowcount > 0  # type: ignore[attr-defined]
