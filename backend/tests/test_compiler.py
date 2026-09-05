from app.buyers.compiler import IntentCompiler


def test_intent_compiler():
    class DummyAdapter:
        def generate(self, prompt, system_prompt):
            raise TimeoutError("Simulated timeout")

    compiler = IntentCompiler(adapter=DummyAdapter())
    import pytest

    from app.buyers.compiler import IntentCompilerError
    with pytest.raises(IntentCompilerError):
        compiler.compile("I want a red laptop", 42)
