import abc
import json
import time
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ModelResponse(BaseModel):
    raw_content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int

class BaseModelAdapter(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> ModelResponse:
        pass

class FakeModelAdapter(BaseModelAdapter):
    """
    Deterministic fake adapter for testing.
    Uses a predefined mapping of prompt snippets to JSON responses.
    """
    def __init__(self):
        self.responses: Dict[str, str] = {}
        self.should_timeout = False
        self.timeout_latency_ms = 5000

    def add_response(self, trigger_text: str, json_response: str):
        self.responses[trigger_text] = json_response

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> ModelResponse:
        start = time.time()
        
        if self.should_timeout:
            # Simulate timeout
            time.sleep(self.timeout_latency_ms / 1000.0)
            raise TimeoutError("Model request timed out.")

        response_text = '{"error": "fake adapter unmatched prompt"}'
        for trigger, response in self.responses.items():
            if trigger in prompt:
                response_text = response
                break
                
        # Simulate small latency
        latency_ms = int((time.time() - start) * 1000) + 10
        
        return ModelResponse(
            raw_content=response_text,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(response_text) // 4,
            latency_ms=latency_ms
        )
