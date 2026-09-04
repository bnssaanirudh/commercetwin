# CommerceTwin — 5-Minute Pitch Script

## 0:00–0:30 (Problem)
"AI-readable does not mean AI-transactable. We are entering the era of Agentic Commerce, but when an AI buyer tries to navigate a messy, real-world catalog, it fails. Worse, merchants don't even know *why* it failed, meaning agentic traffic bounces before it ever hits the checkout."

## 0:30–1:00 (Thesis)
"We built CommerceTwin. It's not another shopping chatbot. It's a digital twin of a merchant that acts as a closed-loop lab. We simulate AI buyers, inject chaos, trace the exact point of failure, automatically synthesize a JSON patch to fix the merchant's catalog, and mathematically verify the repair through counterfactual replay."

## 1:00–1:50 (Successful Journey)
"Here's a successful journey. A buyer wants a 65W USB-C charger. The semantic agent discovers the product, validates the required category and wattage constraints via the state machine, creates the order via Razorpay Test Mode, and pays. Perfect."

## 1:50–2:40 (Chaos & Leak)
"But the real world is messy. Let's trigger our Chaos Engine to delete the typed 'power_watts' attribute, leaving only the unstructured description. The AI buyer immediately aborts. It can't verify safety. The transaction trace records this failure, and our Revenue Leak dashboard instantly flags that ₹2,500 was just lost."

## 2:40–3:25 (Diagnosis & Repair)
"This is where CommerceTwin shines. The localizer traces the leak back to a `MISSING_TYPED_ATTRIBUTE`. Our Repair Synthesizer generates an exact, sandboxed patch to restore the key."

## 3:25–4:05 (Replay Verification)
"We never just blindly apply AI repairs to production. Our system takes the exact failed buyer intent and replays it through the repaired sandbox. You can see it live—the state machine progresses, the transaction succeeds, and the fix is verified."

## 4:05–4:35 (Razorpay & Recovery)
"At the core is our Razorpay integration. Our strict one-way state machine and deterministic WebhookProcessor mean that even if we inject a network timeout mid-payment, idempotency ensures the merchant never double-charges the user."

## 4:35–5:00 (Measured Results & Closing)
"Our evaluation proves it. Standard agents fail on messy data, yielding only a 40% transaction success rate. With CommerceTwin's closed-loop repair and replay, we boost that yield to 85%—all while maintaining 100% intent integrity. We're bridging the gap between AI search and verified commerce. Thank you."
