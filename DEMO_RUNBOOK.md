# CommerceTwin Hero Demo Runbook

This guide covers exactly how to run the deterministic 5-minute presentation pitch demo for CommerceTwin.

## Requirements
- Python 3.12
- The `backend/venv` activated with dependencies installed.
- (Optional) `.env` file containing `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` for real test-mode transactions. If omitted, the demo will gracefully mock the transaction.

## Execution
Run the following from the root directory:
```bash
python scripts/run_demo.py
```

## What Happens in the Demo?
The demo deterministic script executes 10 stages silently under the hood without manual intervention:
1. **Clean Merchant**: Verifies the system is working perfectly.
2. **Catalog Chaos**: Purposely drops the `power_watts` from a top product.
3. **Failed Transaction**: The buyer AI refuses to buy because it cannot verify the wattage.
4. **Localization**: The engine pinpoints `MISSING_TYPED_ATTRIBUTE`.
5. **Revenue Leak**: The exact lost value (₹2,500) is tied to the exact cohort.
6. **Repair Synthesis**: The system proposes a patch to re-add the missing schema key.
7. **Sandbox Application**: The patch is applied into an isolated sandbox environment.
8. **Cohort Replay**: The failed traces are replayed, and now succeed.
9. **Real Transaction**: A Razorpay checkout order is triggered.
10. **Payment Chaos**: An idempotency/duplicate webhook test is forced to prove the merchant policy cannot be corrupted.

## Presenting It
You can run the script live in a terminal window, or point the dashboard at the local backend to watch the Revenue Leak and Repairs sections populate in real-time as the demo script is executed.
