import json
import re

from pydantic import ValidationError

from app.adapters.llm import BaseModelAdapter
from app.buyers.schemas import BuyerIntentSchema


class IntentCompilerError(Exception):
    pass

class IntentSchemaInvalidError(IntentCompilerError):
    def __init__(self, message="INTENT_SCHEMA_INVALID", details=None):
        super().__init__(message)
        self.details = details

class IntentCompiler:
    def __init__(self, adapter: BaseModelAdapter):
        self.adapter = adapter
        self.system_prompt = """
You are an intent compiler for an e-commerce platform.
Convert the user's natural language into the strict JSON schema matching BuyerIntentSchema.
Do not guess missing values. Output MUST be valid JSON.
"""

    def _extract_json(self, raw_content: str) -> str:
        # Strip markdown fences if present
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return raw_content.strip()

    def compile(self, raw_intent: str, seed: int) -> BuyerIntentSchema:
        prompt = f"Raw intent: {raw_intent}\nSeed: {seed}\nOutput JSON:"

        # Initial attempt
        try:
            response = self.adapter.generate(prompt=prompt, system_prompt=self.system_prompt)
            json_str = self._extract_json(response.raw_content)
            data = json.loads(json_str)
            return BuyerIntentSchema(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            # Bounded repair attempt (exactly 1 retry)
            repair_prompt = f"Your previous output failed validation with error: {e!s}\n\nFix the JSON to match the schema for this intent:\n{raw_intent}\nOutput JSON:"
            try:
                repair_response = self.adapter.generate(prompt=repair_prompt, system_prompt=self.system_prompt)
                json_str = self._extract_json(repair_response.raw_content)
                data = json.loads(json_str)
                return BuyerIntentSchema(**data)
            except (json.JSONDecodeError, ValidationError) as repair_e:
                # Repeated failure -> Throw specific error, no guessing
                raise IntentSchemaInvalidError(details=str(repair_e))
        except TimeoutError:
            raise IntentCompilerError("MODEL_TIMEOUT")
        except (OSError, ValueError, AttributeError) as e:
            raise IntentCompilerError(f"UNEXPECTED_ERROR: {e!s}") from e
