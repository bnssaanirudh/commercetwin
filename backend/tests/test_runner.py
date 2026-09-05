import pytest
from app.commerce.runner import CommerceRunner

def test_commerce_runner():
    runner = CommerceRunner(None, None, "test", {})
    assert runner is not None
