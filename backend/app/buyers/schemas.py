from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardConstraints(BaseModel):
    required_categories: list[str] = Field(default_factory=list)
    forbidden_categories: list[str] = Field(default_factory=list)
    forbidden_attributes: dict[str, list[str]] = Field(default_factory=dict)
    required_attributes: dict[str, str] = Field(default_factory=dict)
    min_attributes: dict[str, float] = Field(default_factory=dict) # e.g. {"wattage": 65}
    compatibility: dict[str, str] = Field(default_factory=dict) # e.g. {"connector": "USB-C"}

class SoftPreferences(BaseModel):
    preferred_categories: list[str] = Field(default_factory=list)
    preferred_attributes: dict[str, str] = Field(default_factory=dict)

class BuyerIntentSchema(BaseModel):
    intent_id: str
    raw_intent: str
    hard_constraints: HardConstraints
    soft_preferences: SoftPreferences
    target_budget_paise: int
    max_budget_paise: int
    optional_categories: list[str] = Field(default_factory=list)
    autonomy_level: str
    seed: int
    oracle_valid_product_conditions: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)
