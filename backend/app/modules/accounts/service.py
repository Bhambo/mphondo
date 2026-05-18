import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.accounts.schemas import AccountCreate, AccountUpdate

log = structlog.get_logger()


async def list_accounts(db: AsyncSession, user_id: uuid.UUID) -> list:
    result = await db.execute(
        text("SELECT * FROM v_account_balances WHERE user_id = :uid ORDER BY created_at"),
        {"uid": str(user_id)},
    )
    return list(result.mappings().all())


async def create_account(db: AsyncSession, user_id: uuid.UUID, data: AccountCreate) -> dict:
    result = await db.execute(
        text("""
            INSERT INTO accounts
                (user_id, name, account_type, currency, module_context,
                 iban, phone, color, icon)
            VALUES
                (:uid, :name, :account_type, :currency, :module_context,
                 :iban, :phone, :color, :icon)
            RETURNING *
        """),
        {
            "uid": str(user_id),
            "name": data.name,
            "account_type": data.account_type,
            "currency": data.currency,
            "module_context": data.module_context,
            "iban": data.iban,
            "phone": data.phone,
            "color": data.color,
            "icon": data.icon,
        },
    )
    await db.commit()
    row = result.mappings().one()
    log.info("account_created", account_id=str(row["id"]), user_id=str(user_id))
    return dict(row)


async def update_account(
    db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID, data: AccountUpdate
) -> dict | None:
    fields = data.model_dump(exclude_none=True)
    if not fields:
        return None

    # set_clause is built from model field names only (no user input)
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    params = {**fields, "uid": str(user_id), "aid": str(account_id)}
    query = f"UPDATE accounts SET {set_clause} WHERE id = :aid AND user_id = :uid RETURNING *"  # noqa: S608

    result = await db.execute(text(query), params)
    await db.commit()
    row = result.mappings().one_or_none()
    return dict(row) if row else None
