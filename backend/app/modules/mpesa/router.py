import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.deps import DB, CurrentUser
from app.modules.mpesa import service
from app.modules.mpesa.schemas import (
    ManualEntryCreate,
    ManualEntryOut,
    MpesaRawTxOut,
    StatementUploadOut,
)

router = APIRouter()

_MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/manual", response_model=ManualEntryOut, status_code=status.HTTP_201_CREATED)
async def create_manual_transaction(
    data: ManualEntryCreate,
    db: DB,
    current_user: CurrentUser,
):
    return await service.create_manual_entry(db, current_user, data)


@router.post("/statements/upload", response_model=StatementUploadOut)
async def upload_statement(
    db: DB,
    current_user: CurrentUser,
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    content = await file.read()
    if len(content) > _MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="PDF exceeds 10 MB limit")

    fname = file.filename or "upload.pdf"
    storage_path = f"mpesa/{current_user}/{account_id}/{fname}"
    return await service.ingest_pdf(db, current_user, fname, content, storage_path)


@router.get("/statements/{statement_id}/review", response_model=list[MpesaRawTxOut])
async def list_pending_review(statement_id: uuid.UUID, db: DB, current_user: CurrentUser):
    return await service.list_pending_review(db, current_user, statement_id)


@router.post("/raw/{raw_tx_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_raw_transaction(
    raw_tx_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    mapped_transaction_id: uuid.UUID = Form(...),
):
    ok = await service.confirm_raw_transaction(db, current_user, raw_tx_id, mapped_transaction_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Raw transaction not found")
