import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import TransactionTrace, TraceEvent, FailureCluster, BuyerIntent

class RevenueLeakCalculator:
    def __init__(self, db: Session):
        self.db = db

    def calculate_leak_graph(self):
        """
        Calculates failure clusters and the agentic revenue leak graph.
        Returns the metrics and persists FailureCluster records to DB.
        """
        # Step 1: Find all failed traces (e.g., ABORTED in TraceEvents or TransactionTrace.final_classification)
        failed_traces = self.db.query(TransactionTrace).filter(
            TransactionTrace.final_classification == "FAILED"
        ).all()
        
        clusters = {} # (stage, reason_code) -> {"count": int, "lost_value_paise": int, "trace_ids": list, "buyer_ids": set}
        total_lost_value = 0
        total_failures = 0
        
        for trace in failed_traces:
            # Reconstruct the failure by looking at its events
            events = self.db.query(TraceEvent).filter(
                TraceEvent.trace_id == trace.trace_id
            ).order_by(TraceEvent.event_id.asc()).all()
            
            # Find the state before ABORTED
            last_state = "UNKNOWN"
            reason_code = "UNKNOWN_ERROR"
            
            for event in events:
                if event.event_type == "STATE_ENTERED":
                    state = event.payload.get("state")
                    if state == "ABORTED":
                        reason_code = event.payload.get("details", {}).get("reason", "UNKNOWN_ERROR")
                        break
                    else:
                        last_state = state
            
            # Classify top-level stage
            stage = self._classify_stage(last_state)
            
            # Estimate lost value (look at intent budget or final_amount_paise)
            # Use intent budget as the simulated eligible value
            intent = self.db.query(BuyerIntent).filter(
                BuyerIntent.buyer_id == trace.buyer_id
            ).first()
            
            lost_value = 0
            if intent and intent.budget_paise:
                lost_value = intent.budget_paise
            elif trace.final_amount_paise:
                lost_value = trace.final_amount_paise
            
            key = (stage, reason_code)
            if key not in clusters:
                clusters[key] = {
                    "count": 0,
                    "lost_value_paise": 0,
                    "trace_ids": [],
                    "buyer_ids": set()
                }
                
            clusters[key]["count"] += 1
            clusters[key]["lost_value_paise"] += lost_value
            clusters[key]["trace_ids"].append(trace.trace_id)
            clusters[key]["buyer_ids"].add(trace.buyer_id)
            
            total_lost_value += lost_value
            total_failures += 1
            
        # Clear old failure clusters to regenerate the graph deterministically
        self.db.query(FailureCluster).delete()
        
        results = []
        for (stage, reason_code), data in clusters.items():
            cluster_id = str(uuid.uuid4())
            fc = FailureCluster(
                failure_id=cluster_id,
                taxonomy="REVENUE_LEAK",
                stage=stage,
                reason_code=reason_code,
                estimated_lost_value_paise=data["lost_value_paise"],
                supporting_trace_ids=data["trace_ids"]
            )
            self.db.add(fc)
            
            percentage = 0
            if total_lost_value > 0:
                percentage = (data["lost_value_paise"] / total_lost_value) * 100
                
            results.append({
                "failure_id": cluster_id,
                "stage": stage,
                "reason_code": reason_code,
                "failure_count": data["count"],
                "affected_buyer_count": len(data["buyer_ids"]),
                "simulated_lost_value_paise": data["lost_value_paise"],
                "percentage_of_leak": round(percentage, 2),
                "supporting_traces": data["trace_ids"]
            })
            
        self.db.commit()
        
        # Sort by highest lost value
        results.sort(key=lambda x: x["simulated_lost_value_paise"], reverse=True)
        
        return {
            "total_failures": total_failures,
            "total_simulated_lost_value_paise": total_lost_value,
            "top_clusters": results
        }

    def _classify_stage(self, state_name: str) -> str:
        """
        Classify a detailed state into a top-level stage:
        DISCOVERY / INTERPRETATION / DECISION / COMMERCE / PAYMENT
        """
        if state_name in ["INTENT_RECEIVED"]:
            return "INTERPRETATION"
        elif state_name in ["DISCOVERY"]:
            return "DISCOVERY"
        elif state_name in ["EVALUATION", "SELECTION"]:
            return "DECISION"
        elif state_name in ["CART_CREATED", "PRECHECK"]:
            return "COMMERCE"
        elif state_name in ["READY_FOR_PAYMENT", "PAYMENT", "PAYMENT_PENDING", "AMBIGUOUS_REMOTE_STATE", "RECONCILIATION_REQUIRED"]:
            return "PAYMENT"
        return "UNKNOWN_STAGE"
