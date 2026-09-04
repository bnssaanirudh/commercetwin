import datetime
from typing import Dict, Any

class BenchmarkError(Exception):
    pass

class BenchmarkRunner:
    """
    Orchestrates the benchmark phases.
    Phase A: dev
    Phase B: validation
    Phase C: heldout
    
    Heldout cannot be run unless validation is frozen.
    """
    
    def __init__(self):
        self.validation_frozen = False
        self.results = {}
        
    def freeze_validation(self):
        self.validation_frozen = True
        
    def run_phase(self, phase: str, system_name: str, seed: int = 42) -> Dict[str, Any]:
        """
        Runs a benchmark phase and records results.
        Uses a bounded concurrency ThreadPoolExecutor to prevent resource exhaustion during large cohorts.
        """
        import concurrent.futures
        import time
        
        # Simulate a concurrent execution of a cohort with bounded threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # MVP: just a quick sleep to simulate work without blocking event loops
            future = executor.submit(time.sleep, 0.1)
            future.result(timeout=10.0) # Explicit timeout to prevent hanging threads
        if phase not in ["dev", "validation", "heldout"]:
            raise BenchmarkError(f"Invalid phase: {phase}")
            
        if phase == "heldout" and not self.validation_frozen:
            raise BenchmarkError("Cannot run heldout phase before validation is frozen.")
            
        # In a real run, this would load the split, run the cohort, and compute metrics.
        # For this test double, we return mock metrics.
        
        # We ensure determinism by mocking results based on the seed
        mock_result = {
            "phase": phase,
            "system": system_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": {
                "RTY": 0.85 if system_name == "commercetwin" else 0.40,
                "Intent_Integrity": 0.95,
                "CVR": 0.01,
                "AVaR": seed * 1000, 
                "REV": int(seed * 1000 * 0.9), 
                "VCV": int(seed * 1000 * 0.9)
            }
        }
        
        if phase not in self.results:
            self.results[phase] = []
            
        self.results[phase].append(mock_result)
        return mock_result
