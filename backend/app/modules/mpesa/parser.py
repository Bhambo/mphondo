"""M-Pesa PDF/SMS parser.

Regex patterns calibrated for Vodacom MZ statement format.
OCR fallback (pytesseract) activates when pdfplumber extracts fewer than 5 lines.

NOTE: Patterns will need refinement once real anonymised PDFs are provided.
      Current patterns are based on known M-Pesa MZ SMS format:
      'Voce enviou X MZN para Y. Saldo: Z. Taxa: W. Ref: ABC'
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber
import structlog

from app.core.config import settings

log = structlog.get_logger()

# ── SMS regex ─────────────────────────────────────────────────────────────────
# Format: Voce enviou 500.00 MZN para Joao Silva. Saldo: 1234.56. Taxa: 5.00. Ref: MPSA12345
_SMS_SEND = re.compile(
    r"(?:Voce|Você)\s+enviou\s+"
    r"(?P<amount>[\d,]+\.?\d*)\s+MZN\s+para\s+(?P<counterpart>.+?)\.\s*"
    r"Saldo:\s*(?P<balance>[\d,]+\.?\d*)\.?\s*"
    r"Taxa:\s*(?P<fee>[\d,]+\.?\d*)\.?\s*"
    r"Ref:\s*(?P<ref>\w+)",
    re.IGNORECASE,
)

_SMS_RECEIVE = re.compile(
    r"(?:Voce|Você)\s+recebeu\s+"
    r"(?P<amount>[\d,]+\.?\d*)\s+MZN\s+de\s+(?P<counterpart>.+?)\.\s*"
    r"Saldo:\s*(?P<balance>[\d,]+\.?\d*)\.?\s*"
    r"Ref:\s*(?P<ref>\w+)",
    re.IGNORECASE,
)

# ── PDF table row regex ────────────────────────────────────────────────────────
# Typical PDF columns: Date | Time | Ref | Description | Amount | Balance
_PDF_ROW = re.compile(
    r"(?P<date>\d{2}/\d{2}/\d{4})\s+"
    r"(?P<time>\d{2}:\d{2})\s+"
    r"(?P<ref>\w{6,20})\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>[+-]?[\d,]+\.?\d*)\s+"
    r"(?P<balance>[\d,]+\.?\d*)"
)


@dataclass
class ParsedOperation:
    occurred_at: str | None
    op_type: str | None
    amount: Decimal | None
    counterpart: str | None
    balance_after: Decimal | None
    reference: str | None
    raw_line: str
    confidence: Decimal  # 0.00–1.00


def _to_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


def _infer_op_type(description: str, amount_str: str) -> str:
    desc = description.lower()
    amount = _to_decimal(amount_str) or Decimal(0)

    if "enviou" in desc or "transferência" in desc:
        return "envio_es" if amount < 0 else "recebido"
    if "levantamento" in desc or "levantou" in desc:
        return "saida_diversa"
    if "depósito" in desc or "deposito" in desc:
        return "deposito"
    if "taxa" in desc or "comissão" in desc:
        return "taxa_mpesa"
    if amount < 0:
        return "saida_diversa"
    return "ingresso"


def parse_sms(text: str) -> list[ParsedOperation]:
    results = []

    for match in _SMS_SEND.finditer(text):
        g = match.groupdict()
        results.append(ParsedOperation(
            occurred_at=None,
            op_type="envio_es",
            amount=_to_decimal(g["amount"]),
            counterpart=g["counterpart"].strip(),
            balance_after=_to_decimal(g["balance"]),
            reference=g.get("ref"),
            raw_line=match.group(0),
            confidence=Decimal("0.90"),
        ))

    for match in _SMS_RECEIVE.finditer(text):
        g = match.groupdict()
        results.append(ParsedOperation(
            occurred_at=None,
            op_type="recebido",
            amount=_to_decimal(g["amount"]),
            counterpart=g["counterpart"].strip(),
            balance_after=_to_decimal(g["balance"]),
            reference=g.get("ref"),
            raw_line=match.group(0),
            confidence=Decimal("0.90"),
        ))

    return results


def parse_pdf(file_bytes: bytes) -> list[ParsedOperation]:
    results = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = [ln.strip() for ln in all_text.splitlines() if ln.strip()]

    if len(lines) < 5 and settings.MPESA_PDF_OCR_FALLBACK:
        log.warning("mpesa_pdf_low_lines", count=len(lines), fallback="ocr")
        lines = _ocr_fallback(file_bytes)

    for line in lines:
        match = _PDF_ROW.search(line)
        if not match:
            continue
        g = match.groupdict()
        date_str = g["date"]  # DD/MM/YYYY
        time_str = g["time"]
        try:
            # Convert to ISO8601
            day, month, year = date_str.split("/")
            occurred_at = f"{year}-{month}-{day}T{time_str}:00"
        except ValueError:
            occurred_at = None

        amount = _to_decimal(g["amount"])
        results.append(ParsedOperation(
            occurred_at=occurred_at,
            op_type=_infer_op_type(g["description"], g["amount"]),
            amount=abs(amount) if amount else None,
            counterpart=None,
            balance_after=_to_decimal(g["balance"]),
            reference=g.get("ref"),
            raw_line=line,
            confidence=Decimal("0.75"),
        ))

    log.info("mpesa_pdf_parsed", total=len(results))
    return results


def _ocr_fallback(file_bytes: bytes) -> list[str]:
    try:
        import pytesseract
        from PIL import Image

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            lines = []
            for page in pdf.pages:
                img = page.to_image(resolution=200).original
                text = pytesseract.image_to_string(img, lang="por")
                lines.extend(text.splitlines())
        return [ln.strip() for ln in lines if ln.strip()]
    except Exception as exc:
        log.error("mpesa_ocr_failed", error=str(exc))
        return []
