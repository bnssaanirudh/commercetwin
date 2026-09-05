from pydantic import BaseModel

from app.models import Product, ProductAttribute

from .schemas import BuyerIntentSchema


class ValidationResult(BaseModel):
    is_valid: bool
    reason_code: str | None = None
    failed_constraints: list[str] = []

class IntentOracle:
    def __init__(self, intent: BuyerIntentSchema):
        self.intent = intent

    def _extract_attributes(self, product_attributes: list[ProductAttribute]) -> dict[str, str]:
        extracted = {attr.key: attr.value for attr in product_attributes}
        return extracted

    def evaluate_sku(self, product: Product, product_attributes: list[ProductAttribute]) -> ValidationResult:
        constraints = self.intent.hard_constraints
        attrs = self._extract_attributes(product_attributes)

        # 1. Check forbidden categories
        if product.category in constraints.forbidden_categories:
            return ValidationResult(is_valid=False, reason_code="FORBIDDEN_CATEGORY_PRESENT", failed_constraints=[product.category])

        # 2. Check forbidden attributes
        for forbidden_key, forbidden_values in constraints.forbidden_attributes.items():
            if forbidden_key in attrs and attrs[forbidden_key] in forbidden_values:
                return ValidationResult(is_valid=False, reason_code="FORBIDDEN_ATTRIBUTE_PRESENT", failed_constraints=[f"{forbidden_key}={attrs[forbidden_key]}"])

        # 3. Check required attributes
        for req_key, req_value in constraints.required_attributes.items():
            if req_key not in attrs or attrs[req_key] != req_value:
                return ValidationResult(is_valid=False, reason_code="MISSING_REQUIRED_ATTRIBUTE", failed_constraints=[f"{req_key}={req_value}"])

        # 4. Check minimum attributes (e.g. wattage >= 65)
        for min_key, min_value in constraints.min_attributes.items():
            if min_key not in attrs:
                return ValidationResult(is_valid=False, reason_code="MISSING_MIN_ATTRIBUTE", failed_constraints=[min_key])
            try:
                # Basic float parsing for things like "65W" -> 65.0 or just "65"
                # Strip non-numeric characters for simple cases if needed, but let's assume clean data or simple parsing
                # For robustness, we can strip trailing letters
                import re
                val_str = re.sub(r'[^\d.]+', '', attrs[min_key])
                if float(val_str) < min_value:
                    return ValidationResult(is_valid=False, reason_code="MIN_ATTRIBUTE_NOT_MET", failed_constraints=[f"{min_key} >= {min_value}"])
            except ValueError:
                return ValidationResult(is_valid=False, reason_code="INVALID_ATTRIBUTE_FORMAT", failed_constraints=[min_key])

        # 5. Check compatibility
        for comp_key, comp_value in constraints.compatibility.items():
            if comp_key not in attrs or comp_value not in attrs[comp_key]: # comp_value might be a substring e.g. 'Windows' in 'Windows, macOS'
                return ValidationResult(is_valid=False, reason_code="COMPATIBILITY_MISMATCH", failed_constraints=[f"{comp_key}={comp_value}"])

        return ValidationResult(is_valid=True)

    def evaluate_cart(self, products: list[Product], total_amount_paise: int) -> ValidationResult:
        # 1. Check budget
        if total_amount_paise > self.intent.max_budget_paise:
            return ValidationResult(is_valid=False, reason_code="MAX_BUDGET_EXCEEDED", failed_constraints=[f"Max: {self.intent.max_budget_paise}, Actual: {total_amount_paise}"])

        categories_in_cart = {p.category for p in products}

        # 2. Check forbidden categories
        for forbidden in self.intent.hard_constraints.forbidden_categories:
            if forbidden in categories_in_cart:
                return ValidationResult(is_valid=False, reason_code="FORBIDDEN_CATEGORY_PRESENT", failed_constraints=[forbidden])

        # 3. Check required categories
        for required in self.intent.hard_constraints.required_categories:
            if required not in categories_in_cart:
                return ValidationResult(is_valid=False, reason_code="MISSING_REQUIRED_CATEGORY", failed_constraints=[required])

        return ValidationResult(is_valid=True)
