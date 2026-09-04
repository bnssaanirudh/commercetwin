import pytest
from app.evals.benchmark import BenchmarkRunner, BenchmarkError

def test_benchmark_heldout_lock():
    runner = BenchmarkRunner()
    
    # Dev and validation should run fine
    runner.run_phase("dev", "commercetwin")
    runner.run_phase("validation", "commercetwin")
    
    # Heldout should fail because validation isn't frozen
    with pytest.raises(BenchmarkError, match="Cannot run heldout phase before validation is frozen."):
        runner.run_phase("heldout", "commercetwin")
        
    # Freeze validation
    runner.freeze_validation()
    
    # Now heldout should work
    res = runner.run_phase("heldout", "commercetwin")
    assert res["phase"] == "heldout"

def test_benchmark_reproducibility():
    runner = BenchmarkRunner()
    
    # Same seed should yield same metrics (mocked in our runner)
    res1 = runner.run_phase("dev", "commercetwin", seed=42)
    res2 = runner.run_phase("validation", "commercetwin", seed=42)
    
    assert res1["metrics"]["Synthetic_Captured_Value"] == res2["metrics"]["Synthetic_Captured_Value"]
    
    # Different seed should yield different metrics
    res3 = runner.run_phase("validation", "keyword", seed=99)
    assert res1["metrics"]["Synthetic_Captured_Value"] != res3["metrics"]["Synthetic_Captured_Value"]
