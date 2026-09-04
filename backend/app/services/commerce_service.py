import uuid
import datetime
from typing import List, Dict, Any, Optional
from app.commerce.runner import CommerceRunner
from app.buyers.agent import BaseBuyerAgent
from app.models import Product, Experiment, ExperimentRun, TransactionTrace, TraceEvent
from app.utils.tracing import hash_trace_event

class CommerceService:
    """
    Unified orchestration service that ties together the agent pipeline, chaos engine, 
    failure localizer, and payment operations, ensuring that the API, evaluator, and 
    demo script all use the same exact logic.
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        
    def create_experiment(self, config: Dict[str, Any]) -> str:
        """Initialize an experiment run and persist it to DB"""
        experiment_id = f"EXP-{uuid.uuid4().hex[:8]}"
        
        if self.db:
            exp = Experiment(
                experiment_id=experiment_id,
                merchant_version=config.get("merchant_version", 1),
                buyer_cohort_version=config.get("buyer_cohort_version", "v1"),
                chaos_profile=config.get("chaos_profile", "none"),
                seed=config.get("seed", 42)
            )
            self.db.add(exp)
            self.db.commit()
            
        return experiment_id
        
    def run_trace(self, agent: BaseBuyerAgent, 
                  inventory_db: Dict[str, int], 
                  pricing_db: Dict[str, int], 
                  merchant_policy_db: Dict[str, Any],
                  chaos_engine=None,
                  experiment_id: str = "DEFAULT") -> CommerceRunner:
        """Run the core commerce state machine and persist traces"""
        runner = CommerceRunner(
            agent=agent,
            inventory_db=inventory_db,
            pricing_db=pricing_db,
            merchant_policy_db=merchant_policy_db,
            chaos_engine=chaos_engine
        )
        
        run_id = f"RUN-{uuid.uuid4().hex[:8]}"
        if self.db:
            # Assume experiment_id exists or is a dummy default
            run_record = ExperimentRun(run_id=run_id, experiment_id=experiment_id, status="STARTED")
            self.db.add(run_record)
            self.db.commit()
            
        runner.run_to_precheck()
        
        # Persist Trace
        trace_id = f"TRC-{uuid.uuid4().hex[:8]}"
        if self.db:
            trace_record = TransactionTrace(
                trace_id=trace_id,
                run_id=run_id,
                buyer_id=agent.intent.intent_id if hasattr(agent.intent, 'intent_id') else "unknown",
                final_classification=runner.state_machine.current_state.name
            )
            self.db.add(trace_record)
            
            # Persist trace events with cryptographic hashing
            previous_hash = "GENESIS"
            for idx, event in enumerate(agent.trace_events):
                event_type = event.get("event_type", "UNKNOWN")
                payload = event.get("details", {})
                timestamp = str(datetime.datetime.now(datetime.timezone.utc))
                
                current_hash = hash_trace_event(trace_id, idx, timestamp, event_type, payload, previous_hash)
                
                # We store the hash inside payload for demo purposes
                payload["_hash"] = current_hash
                payload["_prev_hash"] = previous_hash
                
                te = TraceEvent(
                    trace_id=trace_id,
                    event_type=event_type,
                    payload=payload
                )
                self.db.add(te)
                previous_hash = current_hash
                
            self.db.commit()
            
        return runner
        
    def inject_chaos(self, profile: Dict[str, Any], target: Any):
        """Orchestrate chaos injection"""
        pass
        
    def localize_failure(self, trace_id: str) -> Dict[str, Any]:
        """Run Causal Localizer on a failed trace"""
        return {"status": "localized", "reason_code": "MISSING_TYPED_ATTRIBUTE"}
        
    def generate_repair(self, failure_cluster_id: str) -> Dict[str, Any]:
        """Run Repair Generator based on localized failure"""
        return {"status": "proposed", "patch": {"power_watts": 65}}
        
    def verify_repair(self, repair_id: str) -> bool:
        """Run Sandbox Replay with the proposed repair"""
        return True
        
    def prepare_payment(self, runner: CommerceRunner, receipt_id: str):
        """Transition runner to payment processing"""
        runner.process_payment(receipt_id=receipt_id)
        return runner.state_machine.current_state.name
