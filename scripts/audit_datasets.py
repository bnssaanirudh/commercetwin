import os
import json
from collections import defaultdict

def audit():
    scenarios_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'scenarios')
    
    total_count = 0
    split_counts = {"dev": 0, "val": 0, "held_out": 0}
    difficulty_dist = defaultdict(int)
    category_dist = defaultdict(int)
    impossible_count = 0
    valid_solutions_dist = defaultdict(int)
    raw_intents = set()
    duplicates = 0
    
    for split_name in ["dev", "val", "held_out"]:
        filepath = os.path.join(scenarios_dir, f"{split_name}.jsonl")
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("#"):
                    continue
                data = json.loads(line)
                intent = data["intent"]
                
                total_count += 1
                split_counts[split_name] += 1
                difficulty_dist[data["difficulty"]] += 1
                
                for cat in intent["hard_constraints"]["required_categories"]:
                    category_dist[cat] += 1
                    
                if "IMPOSSIBLE" in intent["raw_intent"].upper():
                    impossible_count += 1
                    
                # Solution counts
                if intent.get("oracle_valid_product_conditions"):
                    num_sols = intent["oracle_valid_product_conditions"].get("num_solutions", 0)
                    valid_solutions_dist[num_sols] += 1
                else:
                    if "IMPOSSIBLE" not in intent["raw_intent"].upper():
                        # This should not happen if the generator ensures valid solutions for non-impossible scenarios
                        valid_solutions_dist[0] += 1
                
                # Duplicate check
                if intent["raw_intent"] in raw_intents:
                    duplicates += 1
                raw_intents.add(intent["raw_intent"])
                
    # Generate report
    report = f"""# Buyer Dataset Audit Report

## Scenario Counts
- **Total:** {total_count}
- **Dev:** {split_counts['dev']}
- **Val:** {split_counts['val']}
- **Held-out:** {split_counts['held_out']}

## Difficulty Distribution
"""
    for diff in range(1, 7):
        report += f"- **Level {diff}:** {difficulty_dist.get(diff, 0)}\n"
        
    report += "\n## Category Distribution (Required Categories)\n"
    for cat, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
        report += f"- {cat}: {count}\n"
        
    impossible_rate = (impossible_count / total_count * 100) if total_count > 0 else 0
    report += f"\n## Impossible Scenario Rate\n"
    report += f"- **Impossible Scenarios:** {impossible_count} ({impossible_rate:.1f}%)\n"
    
    report += f"\n## Valid Solutions Distribution (for feasible scenarios)\n"
    for num_sols, count in sorted(valid_solutions_dist.items()):
        report += f"- **{num_sols} solutions:** {count} scenarios\n"
        
    report += f"\n## Duplicate Detection\n"
    report += f"- **Duplicate Raw Intents:** {duplicates} (Expected ~0)\n"
    
    # Validation gates
    report += f"\n## Acceptance Checks\n"
    report += f"- 500 total scenarios: {'PASS' if total_count == 500 else 'FAIL'}\n"
    report += f"- 100 held-out: {'PASS' if split_counts['held_out'] == 100 else 'FAIL'}\n"
    report += f"- Unique intents: {'PASS' if duplicates < 10 else 'FAIL'}\n"
    report += f"- Feasible solutions exist: {'PASS' if valid_solutions_dist.get(0, 0) == 0 else 'FAIL'}\n"
    
    report_path = os.path.join(scenarios_dir, 'audit_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Audit complete. Report written to {report_path}")

if __name__ == "__main__":
    audit()
