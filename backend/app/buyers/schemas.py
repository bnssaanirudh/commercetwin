from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class HardConstraints(BaseModel):
    required_categories: List[str] = Field(default_factory=list)
    forbidden_categories: List[str] = Field(default_factory=list)
    forbidden_attributes: Dict[str, List[str]] = Field(default_factory=dict)
    required_attributes: Dict[str, str] = Field(default_factory=dict)
    min_attributes: Dict[str, float] = Field(default_factory=dict) # e.g. {"wattage": 65}
    compatibility: Dict[str, str] = Field(default_factory=dict) # e.g. {"connector": "USB-C"}

class SoftPreferences(BaseModel):
    preferred_categories: List[str] = Field(default_factory=list)
    preferred_attributes: Dict[str, str] = Field(default_factory=dict)

class BuyerIntentSchema(BaseModel):
    intent_id: str
    raw_intent: str
    hard_constraints: HardConstraints
    soft_preferences: SoftPreferences
    target_budget_paise: int
    max_budget_paise: int
    optional_categories: List[str] = Field(default_factory=list)
    autonomy_level: str
    seed: int
    oracle_valid_product_conditions: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
