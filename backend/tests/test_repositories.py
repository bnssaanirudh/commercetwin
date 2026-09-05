from app.db import engine, get_db
from app.models import Base
from app.repositories import MerchantRepository, PaymentRepository, TraceRepository


def test_repositories():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    repo = MerchantRepository(db)
    assert repo.get_merchant("fake") is None
    assert repo.get_product("fake") is None
    assert repo.get_pricing("fake") is None
    assert repo.get_inventory("fake") is None

    pay_repo = PaymentRepository(db)
    assert pay_repo is not None

    trace_repo = TraceRepository(db)
    assert trace_repo is not None
