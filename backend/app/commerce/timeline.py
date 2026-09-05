from typing import Any


class TraceTimelineRenderer:
    @staticmethod
    def render(trace_data: dict[str, Any]) -> str:
        lines = []
        lines.append(f"Trace ID: {trace_data['trace_id']}")
        lines.append(f"Experiment ID: {trace_data['experiment_id']}")
        lines.append(f"Buyer Config: {trace_data['buyer_config']}")
        lines.append("-" * 40)

        for event in trace_data['events']:
            ts = event['timestamp']
            ev_type = event['event_type']
            payload = event['payload']

            time_str = ts.split('T')[1][:8] # HH:MM:SS

            if ev_type == "STATE_ENTERED":
                lines.append(f"[{time_str}] [STATE] {payload.get('state')}")
                if payload.get("details") and "reason" in payload["details"]:
                    lines.append(f"  -> Reason: {payload['details']['reason']}")
            elif ev_type == "CANDIDATE_REJECTED":
                sku = payload.get("sku", "Unknown")
                reason = payload.get("reason_code", "Unknown")
                lines.append(f"[{time_str}] [EVALUATION] Rejected {sku} ({reason})")
            elif ev_type == "CART_FINALIZED":
                skus = payload.get("skus", [])
                lines.append(f"[{time_str}] [SELECTION] Cart finalized with {len(skus)} items: {', '.join(skus)}")
            elif ev_type == "MODEL_CALL":
                lines.append(f"[{time_str}] [LLM] Called model {payload.get('model')}")
            else:
                lines.append(f"[{time_str}] [{ev_type}] {payload}")

        lines.append("-" * 40)
        lines.append(f"Final State: {trace_data['final_state']}")

        return "\n".join(lines)
