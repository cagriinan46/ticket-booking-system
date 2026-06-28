import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from routers import events


class AIChatHelpersTest(unittest.TestCase):
    def test_normalize_ai_intent_cleans_filters_and_preserves_follow_up(self):
        payload = {
            "city": "null",
            "category": "Konser",
            "start_date": "",
            "end_date": "belirtilmemiş",
            "needs_clarification": True,
            "follow_up_question": "Hangi şehirde konser arıyorsunuz?",
        }

        normalized = events.normalize_ai_intent(payload)

        self.assertIsNone(normalized["city"])
        self.assertEqual(normalized["category"], "Konser")
        self.assertIsNone(normalized["start_date"])
        self.assertIsNone(normalized["end_date"])
        self.assertTrue(normalized["needs_clarification"])
        self.assertEqual(
            normalized["follow_up_question"],
            "Hangi şehirde konser arıyorsunuz?",
        )

    def test_build_ai_chat_reply_uses_follow_up_when_clarification_needed(self):
        intent = {
            "city": None,
            "category": "Konser",
            "start_date": None,
            "end_date": None,
            "needs_clarification": True,
            "follow_up_question": "Hangi şehirde konser arıyorsunuz?",
        }

        reply = events.build_ai_chat_reply([], intent)

        self.assertEqual(reply, "Hangi şehirde konser arıyorsunuz?")

    def test_build_ai_chat_reply_explains_matching_results(self):
        intent = {
            "city": "İstanbul",
            "category": "Konser",
            "start_date": None,
            "end_date": None,
            "needs_clarification": False,
            "follow_up_question": None,
        }

        reply = events.build_ai_chat_reply([object(), object()], intent)

        self.assertIn("2 etkinlik", reply)
        self.assertIn("İstanbul", reply)
        self.assertIn("Konser", reply)

    def test_ai_chat_returns_follow_up_without_querying_database(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="Bir şeyler bakıyorum")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages: {
                "city": None,
                "category": None,
                "start_date": None,
                "end_date": None,
                "needs_clarification": True,
                "follow_up_question": "Hangi şehirde etkinlik arıyorsunuz?",
            }

            def fail_if_queried(db, filters):
                raise AssertionError("Database should not be queried")

            events.query_events_by_filters = fail_if_queried

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertTrue(response["needs_clarification"])
        self.assertEqual(response["events"], [])
        self.assertEqual(response["reply"], "Hangi şehirde etkinlik arıyorsunuz?")

    def test_ai_search_keeps_existing_shape_and_adds_filters_applied(self):
        request = events.AISearchRequest(prompt="İstanbul'da konser var mı?")
        intent = {
            "city": "İstanbul",
            "category": "Konser",
            "start_date": None,
            "end_date": None,
            "needs_clarification": False,
            "follow_up_question": None,
        }

        original_extract = events.extract_ai_search_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_search_intent = lambda prompt: intent
            events.query_events_by_filters = lambda db, filters: []

            response = events.ai_search_events(request, db=object())
        finally:
            events.extract_ai_search_intent = original_extract
            events.query_events_by_filters = original_query

        expected_filters = {
            "city": "İstanbul",
            "category": "Konser",
            "start_date": None,
            "end_date": None,
        }
        self.assertEqual(response["llm_extracted_data"], expected_filters)
        self.assertEqual(response["filters_applied"], expected_filters)
        self.assertEqual(response["events"], [])


if __name__ == "__main__":
    unittest.main()
