import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DB, CurrentUser
from app.modules.ledger import service
from app.modules.ledger.schemas import TransactionCreate, TransactionOut

router = APIRouter()


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    db: DB,
    current_user: CurrentUser,
    module: str | None = Query(None, pattern="^(mz|es)$"),
    account_id: uuid.UUID | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list_transactions(
        db, current_user, module, account_id, category_id, from_date, to_date, limit, offset
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(data: TransactionCreate, db: DB, current_user: CurrentUser):
    return await service.create_transaction(db, current_user, data)


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(tx_id: uuid.UUID, db: DB, current_user: CurrentUser):
    tx = await service.get_transaction(db, current_user, tx_id)
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(tx_id: uuid.UUID, db: DB, current_user: CurrentUser):
    deleted = await service.soft_delete_transaction(db, current_user, tx_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
