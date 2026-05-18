"""M-Pesa SMS parser unit tests."""

from decimal import Decimal

from app.modules.mpesa.parser import parse_sms


def test_parse_sms_send():
    sms = "Voce enviou 500.00 MZN para Joao Silva. Saldo: 1234.56. Taxa: 5.00. Ref: MPSA12345"
    ops = parse_sms(sms)
    assert len(ops) == 1
    op = ops[0]
    assert op.op_type == "envio_es"
    assert op.amount == 500
    assert op.counterpart == "Joao Silva"
    assert op.reference == "MPSA12345"
    assert op.balance_after == Decimal("1234.56")


def test_parse_sms_receive():
    sms = "Você recebeu 200.00 MZN de Maria Costa. Saldo: 800.00. Ref: RCVD98765"
    ops = parse_sms(sms)
    assert len(ops) == 1
    op = ops[0]
    assert op.op_type == "recebido"
    assert op.amount == 200
    assert op.counterpart == "Maria Costa"


def test_parse_sms_no_match():
    ops = parse_sms("Mensagem aleatória sem formato M-Pesa")
    assert ops == []


def test_parse_sms_multiple():
    sms = """Voce enviou 100.00 MZN para A. Saldo: 900.00. Taxa: 1.00. Ref: REF001
             Você recebeu 50.00 MZN de B. Saldo: 950.00. Ref: REF002"""
    ops = parse_sms(sms)
    assert len(ops) == 2
