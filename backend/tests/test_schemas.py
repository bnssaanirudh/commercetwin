from app.schemas import PaymentOperationCreate, ProductBase, RepairProposalBase

def test_schemas():
    payment = PaymentOperationCreate(
        trace_id="1", amount_paise=1000, state="PENDING", payment_operation_fingerprint="fp1"
    )
    assert payment.trace_id == "1"
    
    product = ProductBase(sku="SKU-1", title="Product 1", category="Cat 1")
    assert product.sku == "SKU-1"

    repair = RepairProposalBase(
        failure_id="f1", repair_type="type1", proposed_patch={}
    )
    assert repair.failure_id == "f1"
