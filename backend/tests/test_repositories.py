from app.repositories import MerchantRepository, PaymentRepository, TraceRepository
from app.db import get_db

from app.db import get_db, engine
from app.models import Base

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
