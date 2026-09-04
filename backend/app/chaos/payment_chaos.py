import requests

class PaymentChaosAdapter:
    """
    Simulates chaotic network conditions when interacting with remote financial APIs.
    """
    def __init__(self, razorpay_service):
        self.service = razorpay_service
        self.injected_fault = None

    def inject_fault(self, fault_type: str):
        """
        Supports: 'TIMEOUT', 'DROP_RESPONSE_AFTER_SUCCESS', '5XX_ERROR'
        """
        self.injected_fault = fault_type

    def create_order(self, amount_paise: int, receipt: str, notes: dict = None):
        if self.injected_fault == "TIMEOUT":
            self.injected_fault = None
            raise requests.exceptions.ReadTimeout("Simulated network timeout before response.")
            
        if self.injected_fault == "5XX_ERROR":
            self.injected_fault = None
            raise requests.exceptions.HTTPError("Simulated 503 Service Unavailable")
            
        if self.injected_fault == "DROP_RESPONSE_AFTER_SUCCESS":
            self.injected_fault = None
            # Execute the real operation
            self.service.create_order(amount_paise, receipt, notes)
            # But drop the response (simulate timeout returning to client)
            raise requests.exceptions.ReadTimeout("Simulated network drop after successful server execution.")
            
        # Normal execution
        return self.service.create_order(amount_paise, receipt, notes)
