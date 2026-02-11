"""
unit tests for the AI assistant module.
tests routine handling and fallback mechanisms.
"""

import unittest
from unittest.mock import patch, MagicMock
from ai.assistant import AIAssistant


class TestAIAssistant(unittest.TestCase):

    def test_init_disabled_if_no_key(self):
        # ensure GEMINI_AVAILABLE doesn't crash the test if not installed
        with patch("ai.assistant.GEMINI_AVAILABLE", True):
            assistant = AIAssistant(api_key=None)
            self.assertFalse(assistant.enabled)

    def test_init_enabled_if_key_provided(self):
        with patch("ai.assistant.GEMINI_AVAILABLE", True):
            with patch("ai.assistant.genai.Client") as mock_client:
                assistant = AIAssistant(api_key="fake_key")
                self.assertTrue(assistant.enabled)

    def test_fallback_routine_bedtime(self):
        assistant = AIAssistant(api_key=None)
        result = assistant.handle_routine("Bedtime")
        
        self.assertIn("actions", result)
        self.assertEqual(len(result["actions"]), 2)
        # check one of the actions
        self.assertEqual(result["actions"][0]["args"]["item_name"], "LivingRoom_Light")
        self.assertEqual(result["actions"][0]["function"], "turn_off")

    def test_fallback_routine_invalid(self):
        assistant = AIAssistant(api_key=None)
        result = assistant.handle_routine("Unknown")
        self.assertIn("no default routine", result["log_message"].lower())
        self.assertEqual(len(result["actions"]), 0)

    @patch("ai.assistant.genai.Client")
    def test_gemini_call_success(self, mock_genai_client_cls):
        # mock the gemini client and its complex response structure
        mock_client = MagicMock()
        mock_genai_client_cls.return_value = mock_client
        
        # mock complete_execution response structure:
        # response.candidates -> parts -> function_call
        mock_part = MagicMock()
        mock_part.function_call.name = "toggle"
        mock_part.function_call.args = {"item_name": "TestItem"}
        mock_part.text = "AI message"
        
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response

        with patch("ai.assistant.GEMINI_AVAILABLE", True):
            assistant = AIAssistant(api_key="fake_key")
            result = assistant.handle_routine("CustomRoutine")

            self.assertEqual(result["log_message"], "AI message")
            self.assertEqual(result["actions"][0]["function"], "toggle")

    @patch("ai.assistant.genai.Client")
    def test_gemini_call_failure_triggers_fallback(self, mock_genai_client_cls):
        mock_client = MagicMock()
        mock_genai_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API error")

        with patch("ai.assistant.GEMINI_AVAILABLE", True):
            assistant = AIAssistant(api_key="fake_key")
            # should catch exception and use fallback
            result = assistant.handle_routine("Bedtime")
            
            self.assertEqual(len(result["actions"]), 2)
            self.assertIn("bedtime routine", result["log_message"].lower())


if __name__ == "__main__":
    unittest.main()
