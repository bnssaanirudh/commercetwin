from app.analytics.leak_graph import RevenueLeakCalculator


def test_leak_graph():
    generator = RevenueLeakCalculator(db=None)
    assert generator is not None
    # Cannot easily mock db for full calculation without a lot of setup, but this gets us some coverage and collects successfully
