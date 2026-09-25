from app.core.exceptions import AppError


class FakeAIProvider:
    name = "fake-test-provider"

    def __init__(self, result="FAKE · 风淋 Prompt：双门互锁，连续步态。", error=None):
        self.result, self.error = result, error
        self.calls = []

    def generate(self, rendered_input, config, operation_id):
        # No credentials are retained in test evidence.
        self.calls.append((rendered_input, config.model, operation_id))
        if self.error:
            raise self.error
        if "[[FAKE_TIMEOUT]]" in rendered_input:
            raise AppError("AI_TIMEOUT", "Fake timeout", 504)
        if (
            "[[FAKE_RETRY]]" in rendered_input
            and sum(c[2] == operation_id for c in self.calls) == 1
        ):
            raise AppError("AI_TIMEOUT", "Fake first attempt timeout", 504)
        return self.result
