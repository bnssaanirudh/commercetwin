import os
import time

import httpx

from app.adapters.llm import BaseModelAdapter, ModelResponse


class OpenAIAdapter(BaseModelAdapter):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if not self.api_key:
            raise ValueError("LLM_API_KEY must be set for real model adapter.")

    def generate(self, prompt: str, system_prompt: str | None = None) -> ModelResponse:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }

        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            raise TimeoutError("Model request timed out.")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Model API error: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling Model API: {e!s}")

        latency_ms = int((time.time() - start_time) * 1000)

        choice = data.get("choices", [{}])[0].get("message", {})
        raw_content = choice.get("content", "{}")
        usage = data.get("usage", {})

        return ModelResponse(
            raw_content=raw_content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms
        )
