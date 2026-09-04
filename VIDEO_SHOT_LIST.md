# Video Shot List

**Requirements**: Screen recording with terminal and browser visible side-by-side.

| Time | Exact Screen | Exact Command/Click | Expected Result | Fallback |
|------|-------------|---------------------|-----------------|----------|
| 0:00 | Terminal (Left) | `python scripts/run_demo.py` | Script boots up and begins Stage 1. | Run pre-recorded local artifact. |
| 0:45 | Terminal (Left) | Observe Stage 1 output | Shows `READY_FOR_PAYMENT`. | Keep playing recording. |
| 1:50 | Terminal (Left) | Observe Stage 2 & 3 | Shows Catalog Chaos and `ABORTED`. | Keep playing recording. |
| 2:45 | Terminal (Left) | Observe Stage 4 & 5 | Shows `MISSING_TYPED_ATTRIBUTE` and INR 2500 leaked. | Keep playing recording. |
| 3:25 | Terminal (Left) | Observe Stage 6 & 7 | Shows synthesized JSON patch applied to Sandbox. | Keep playing recording. |
| 3:45 | Terminal (Left) | Observe Stage 8 | Shows Replay outcome: `READY_FOR_PAYMENT`. | Keep playing recording. |
| 4:10 | Terminal (Left) | Observe Stage 9 & 10 | Shows Razorpay Order creation and Idempotency ignoring duplicate webhooks. | Keep playing recording. |
| 4:35 | Dashboard UI (Right)| Refresh Dashboard | Charts update to show the 85% RTY and fixed leak. | Static screenshot of dashboard. |

## 30-Second Backup Demo Sequence
If the terminal breaks or Razorpay API is unreachable during a live demo:
1. Open the `/frontend` Dashboard.
2. Show the pre-populated "Revenue Leak" chart.
3. Click on the most recent trace to show the "MISSING_TYPED_ATTRIBUTE" failure.
4. Show the "Repairs" tab where the patch is marked as "Verified via Replay."
*(Acknowledge this is running on pre-recorded local artifacts for speed).*
