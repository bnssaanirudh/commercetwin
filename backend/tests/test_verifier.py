from app.analytics.verifier import RepairVerifier


def test_repair_verifier():
    verifier = RepairVerifier()
    assert verifier is not None
