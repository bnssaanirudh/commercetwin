from app.buyers.compiler import IntentCompiler
from app.buyers.schemas import BuyerIntentSchema
from app.adapters.openai_adapter import OpenAIAdapter

def test_intent_compiler():
    class DummyAdapter:
        def generate(self, prompt, system_prompt):
            raise TimeoutError("Simulated timeout")
    
    compiler = IntentCompiler(adapter=DummyAdapter())
    import pytest
    from app.buyers.compiler import IntentCompilerError
    with pytest.raises(IntentCompilerError):
        res = compiler.compile("I want a red laptop", 42)
