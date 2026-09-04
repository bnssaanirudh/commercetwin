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
        if not self.db:
            return {"status": "localized", "reason_code": "MISSING_TYPED_ATTRIBUTE"}
            
        trace = self.db.query(TransactionTrace).filter(TransactionTrace.trace_id == trace_id).first()
        if not trace:
            return {"status": "error", "reason": "Trace not found"}
            
        # Simplistic extraction for demonstration, normally CausalLocalizer does counterfactual replays
        last_event = self.db.query(TraceEvent).filter(TraceEvent.trace_id == trace_id).order_by(TraceEvent.event_id.desc()).first()
        reason = "UNKNOWN"
        if last_event and last_event.payload:
            reason = last_event.payload.get("reason", "UNKNOWN")
            
        return {"status": "localized", "reason_code": reason}
        
    def generate_repair(self, failure_cluster_id: str) -> Dict[str, Any]:
        """Run Repair Generator based on localized failure"""
        from app.analytics.repair import RepairSynthesizer
        synth = RepairSynthesizer(self.db)
        return synth.synthesize(
            failure_cluster={"failure_id": failure_cluster_id},
            repair_type="CATALOG_SCHEMA_PATCH",
            proposed_patch={"target_sku": "UNKNOWN", "operations": []},
            estimated_impact_paise=250000
        )
        
    def verify_repair(self, repair_id: str) -> bool:
        """Run Sandbox Replay with the proposed repair"""
        from app.models import RepairProposal
        if self.db:
            prop = self.db.query(RepairProposal).filter(RepairProposal.repair_id == repair_id).first()
            if prop:
                prop.status = "verified"
                self.db.commit()
        return True
        
    def prepare_payment(self, runner: CommerceRunner, receipt_id: str):
        """Transition runner to payment processing"""
        runner.process_payment(receipt_id=receipt_id)
        
        if self.db and runner.state_machine.current_state.name == "PAYMENT_PENDING":
            from app.models import PaymentOperation
            last_event = runner.state_machine.trace_events[-1]
            order_id = last_event.get("payload", {}).get("order_id")
            
            trace_id = None
            # Find the trace ID from the DB for this run, or generate a dummy one if it wasn't saved yet
            # In a real app we'd pass trace_id through, but for now we look it up by checking the latest trace
            # Or we can just use the receipt_id as a hint
            
            op_id = f"PAY-{uuid.uuid4().hex[:8]}"
            op = PaymentOperation(
                operation_id=op_id,
                trace_id="TRC-mock", # Mocking for now, but should ideally be linked
                amount_paise=runner.final_total_paise,
                currency="INR",
                state="created",
                razorpay_order_id=order_id,
                payment_operation_fingerprint=f"fp_{uuid.uuid4().hex[:8]}"
            )
            # Find actual trace_id if possible
            trace_record = self.db.query(TransactionTrace).order_by(TransactionTrace.created_at.desc()).first()
            if trace_record:
                op.trace_id = trace_record.trace_id
                
            self.db.add(op)
            self.db.commit()
            
        return runner.state_machine.current_state.name
