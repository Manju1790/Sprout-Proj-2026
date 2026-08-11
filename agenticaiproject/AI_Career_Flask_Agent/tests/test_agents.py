import unittest
from unittest import mock

import agents


class AskFallbackTests(unittest.TestCase):
    def test_ask_returns_fallback_when_llm_fails(self):
        class FailingLLM:
            def invoke(self, prompt):
                raise RuntimeError("network unavailable")

        with mock.patch("agents.llm", FailingLLM()):
            result = agents.ask("Analyze this candidate profile")

        self.assertIn("Fallback", result)
        self.assertIn("AI service", result)


if __name__ == "__main__":
    unittest.main()
