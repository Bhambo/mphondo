import hashlib
import uuid
from decimal import Decimal

import structlog
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ledger import service as ledger_service
from app.modules.ledger.schemas import CurrencyCode, EntryIn, TransactionCreate
from app.modules.mpesa import parser as mpesa_parser
from app.modules.mpesa.schemas import ManualEntryCreate

log = structlog.get_logger()

_ACCOUNT_TYPE_BY_MODULE = {"mz": "mpesa", "es": "bank_es"}


async def _get_or_create_virtual(
    db: AsyncSession, user_id: uuid.UUID, virtual_type: str, module: str, currency: str
) -> uuid.UUID:
    result = await db.execute(
        text("""
            SELECT id FROM accounts
            WHERE user_id = :uid AND account_type = :vtype AND module_context = :mod
            ORDER BY created_at LIMIT 1
        """),
        {"uid": str(user_id), "vtype": virtual_type, "mod": module},
    )
    row = result.mappings().one_or_none()
    if row:
        return row["id"]

    name = "Receitas" if virtual_type == "virtual_income" else "Despesas"
    insert = await db.execute(
        text("""
            INSERT INTO accounts (user_id, name, account_type, currency, module_context)
            VALUES (:uid, :name, :vtype, :currency, :mod)
            RETURNING id
        """),
        {
            "uid": str(user_id),
            "name": name,
            "vtype": virtual_type,
            "currency": currency,
            "mod": module,
        },
    )
    await db.commit()
    return insert.scalar_one()


async def create_manual_entry(
    db: AsyncSession, user_id: uuid.UUID, data: ManualEntryCreate
) -> dict:
    currency: CurrencyCode = "MZN" if data.module == "mz" else "EUR"
    acct_type = _ACCOUNT_TYPE_BY_MODULE[data.module]

    real_row = (
        (
            await db.execute(
                text("""
                SELECT id FROM accounts
                WHERE user_id = :uid AND account_type = :atype
                  AND module_context = :mod AND is_active = true AND deleted_at IS NULL
                ORDER BY sort_order, created_at LIMIT 1
            """),
                {"uid": str(user_id), "atype": acct_type, "mod": data.module},
            )
        )
        .mappings()
        .one_or_none()
    )

    if not real_row:
        raise HTTPException(
            status_code=404,
            detail=f"No active {acct_type} account for module '{data.module}'. Create one first.",
        )
    real_id = real_row["id"]

    virtual_type = "virtual_income" if data.direction == "entrada" else "virtual_expense"
    virt_id = await _get_or_create_virtual(db, user_id, virtual_type, data.module, currency)

    # entrada: money arrives in real account → CREDIT real, DEBIT virtual_income
    # saida:   money leaves real account    → DEBIT real,  CREDIT virtual_expense
    if data.direction == "entrada":
        entries = [
            EntryIn(account_id=real_id, direction="credit", amount=data.amount),
            EntryIn(account_id=virt_id, direction="debit", amount=data.amount),
        ]
    else:
        entries = [
            EntryIn(account_id=real_id, direction="debit", amount=data.amount),
            EntryIn(account_id=virt_id, direction="credit", amount=data.amount),
        ]

    tx_create = TransactionCreate(
        description=data.description,
        occurred_at=data.occurred_at,
        module=data.module,
        currency=currency,
        reference=data.reference,
        notes=data.counterpart,
        entries=entries,
    )
    tx = await ledger_service.create_transaction(db, user_id, tx_create)
    return {"transaction_id": tx["id"]}


async def ingest_pdf(
    db: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
    storage_path: str,
) -> dict:
    """Store PDF statement record and parse operations into mpesa_raw_transactions."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Detect duplicate upload
    existing = await db.execute(
        text("SELECT id FROM mpesa_statements WHERE user_id = :uid AND file_hash = :hash"),
        {"uid": str(user_id), "hash": file_hash},
    )
    if existing.scalar_one_or_none():
        return {"error": "duplicate", "message": "Este archivo ya fue cargado anteriormente."}

    result = await db.execute(
        text("""
            INSERT INTO mpesa_statements
                (user_id, filename, storage_path, file_hash, status)
            VALUES (:uid, :filename, :storage_path, :file_hash, 'uploaded')
            RETURNING id
        """),
        {
            "uid": str(user_id),
            "filename": filename,
            "storage_path": storage_path,
            "file_hash": file_hash,
        },
    )
    await db.commit()
    statement_id = result.scalar_one()

    # Parse inline for now; Sprint 3 will move this to Arq worker
    ops = mpesa_parser.parse_pdf(file_bytes)
    parsed_count = 0
    needs_review = 0

    for op in ops:
        await _store_parsed_ops(db, statement_id, [op])
        parsed_count += 1
        if op.confidence < Decimal("0.85"):
            needs_review += 1

    await db.execute(
        text("""
            UPDATE mpesa_statements
            SET status = 'parsed', parsed_at = NOW(), raw_count = :count
            WHERE id = :id
        """),
        {"id": str(statement_id), "count": parsed_count},
    )
    await db.commit()

    return {
        "statement_id": statement_id,
        "filename": filename,
        "parsed_count": parsed_count,
        "needs_review_count": needs_review,
        "message": f"Parsed {parsed_count} operations ({needs_review} need review)",
    }


async def _store_parsed_ops(
    db: AsyncSession,
    statement_id: uuid.UUID,
    ops: list,
) -> None:
    """Insert parsed operations into mpesa_raw_transactions (aligns with schema columns)."""
    for op in ops:
        await db.execute(
            text("""
                INSERT INTO mpesa_raw_transactions
                    (statement_id, user_id, raw_ref, raw_type, raw_amount,
                     raw_balance, raw_party, raw_date, raw_description)
                SELECT
                    :sid,
                    s.user_id,
                    :raw_ref,
                    :raw_type,
                    :raw_amount,
                    :raw_balance,
                    :raw_party,
                    :raw_date::timestamptz,
                    :raw_description
                FROM mpesa_statements s WHERE s.id = :sid
                ON CONFLICT (user_id, raw_ref) WHERE raw_ref IS NOT NULL DO NOTHING
            """),
            {
                "sid": str(statement_id),
                "raw_ref": op.reference,
                "raw_type": op.op_type,
                "raw_amount": op.amount,
                "raw_balance": op.balance_after,
                "raw_party": op.counterpart,
                "raw_date": op.occurred_at,
                "raw_description": op.raw_line[:500] if op.raw_line else None,
            },
        )


async def list_pending_review(
    db: AsyncSession, user_id: uuid.UUID, statement_id: uuid.UUID
) -> list:
    result = await db.execute(
        text("""
            SELECT r.* FROM mpesa_raw_transactions r
            JOIN mpesa_statements s ON s.id = r.statement_id
            WHERE s.id = :sid AND s.user_id = :uid
              AND r.transaction_id IS NULL    -- no confirmadas aún
              AND r.is_duplicate = false
            ORDER BY r.raw_date
        """),
        {"sid": str(statement_id), "uid": str(user_id)},
    )
    return list(result.mappings().all())


async def confirm_raw_transaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    raw_tx_id: uuid.UUID,
    mapped_tx_id: uuid.UUID,
) -> bool:
    result = await db.execute(
        text("""
            UPDATE mpesa_raw_transactions r
            SET transaction_id = :tx_id
            FROM mpesa_statements s
            WHERE r.id = :rid AND r.statement_id = s.id AND s.user_id = :uid
            RETURNING r.id
        """),
        {"rid": str(raw_tx_id), "tx_id": str(mapped_tx_id), "uid": str(user_id)},
    )
    await db.commit()
    return result.rowcount > 0  # type: ignore[attr-defined]
