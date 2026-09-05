import csv
import io
import json
from typing import Any


class MetricsReporter:
    """Exports computed metrics to JSON, CSV, and Markdown."""

    @staticmethod
    def to_json(metrics: dict[str, Any], indent: int = 2) -> str:
        return json.dumps(metrics, indent=indent)

    @staticmethod
    def to_csv(metrics: dict[str, Any]) -> str:
        rows = []
        # Flatten top-level scalar metrics
        for key, val in metrics.items():
            if isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    rows.append({"metric": f"{key}.{sub_key}", "value": sub_val})
            else:
                rows.append({"metric": key, "value": val})

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    @staticmethod
    def to_markdown(metrics: dict[str, Any]) -> str:
        lines = ["# CommerceTwin Metrics Report\n"]
        note = metrics.get("note", "")
        if note:
            lines.append(f"> **{note}**\n")

        def _render(d: dict, prefix: str = ""):
            for k, v in d.items():
                if k == "note":
                    continue
                if isinstance(v, dict):
                    lines.append(f"\n## {prefix}{k}")
                    _render(v, prefix="")
                else:
                    lines.append(f"- **{prefix}{k}**: `{v}`")

        _render(metrics)
        return "\n".join(lines)
