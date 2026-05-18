import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MpesaOpType = Literal[
    # Entradas MZ
    "ingresso", "deposito", "devolution", "recebido",
    # Saídas MZ
    "envio_es", "xitiqui_out", "emprestimo_dado", "compra_pessoal",
    "gasto_familia", "taxa_mpesa", "saida_diversa",
    # Transferências internas
    "transferencia_interna",
]


class MpesaTransactionCreate(BaseModel):
    """Manual entry for an M-Pesa operation."""
    account_id: uuid.UUID
    op_type: MpesaOpType
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    occurred_at: str
    contact_name: str | None = Field(None, max_length=120)
    reference: str | None = Field(None, max_length=100)
    notes: str | None = None
    fx_rate_snapshot: Decimal | None = None   # EUR/MZN at time of operation


class MpesaRawTxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    statement_id: uuid.UUID
    raw_ref: str | None = None
    raw_type: str | None = None
    raw_amount: Decimal | None = None
    raw_balance: Decimal | None = None
    raw_party: str | None = None
    raw_date: str | None = None
    raw_description: str | None = None
    confidence: Decimal = Decimal("0")
    is_duplicate: bool = False
    transaction_id: uuid.UUID | None = None


class StatementUploadOut(BaseModel):
    statement_id: uuid.UUID
    filename: str
    parsed_count: int
    needs_review_count: int
    message: str
