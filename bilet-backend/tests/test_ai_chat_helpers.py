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

    def test_normalize_ai_chat_intent_resets_filters_without_searching(self):
        payload = {
            "intent": "reset_filters",
            "filters": {
                "city": None,
                "category": None,
                "start_date": None,
                "end_date": None,
            },
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Filtreleri temizledim.",
        }
        current_filters = {
            "city": "İstanbul",
            "category": "Konser",
            "start_date": None,
            "end_date": None,
        }

        normalized = events.normalize_ai_chat_intent(payload, current_filters)

        self.assertEqual(normalized["intent"], "reset_filters")
        self.assertEqual(normalized["filters"], {
            "city": None,
            "category": None,
            "start_date": None,
            "end_date": None,
        })
        self.assertFalse(normalized["should_search"])
        self.assertFalse(normalized["needs_clarification"])
        self.assertEqual(normalized["assistant_reply"], "Filtreleri temizledim.")

    def test_normalize_ai_chat_intent_merges_filter_update_without_searching(self):
        payload = {
            "intent": "update_filters",
            "filters": {
                "city": "İstanbul",
                "category": None,
                "start_date": None,
                "end_date": None,
            },
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "İstanbul'u filtrelere ekledim, henüz arama yapmıyorum.",
        }
        current_filters = {
            "city": None,
            "category": "Konser",
            "start_date": None,
            "end_date": None,
        }

        normalized = events.normalize_ai_chat_intent(payload, current_filters)

        self.assertEqual(normalized["intent"], "update_filters")
        self.assertEqual(normalized["filters"], {
            "city": "İstanbul",
            "category": "Konser",
            "start_date": None,
            "end_date": None,
        })
        self.assertFalse(normalized["should_search"])

    def test_normalize_ai_chat_intent_preserves_clarification_for_filter_answer(self):
        payload = {
            "intent": "update_filters",
            "filters": {
                "city": None,
                "category": "Konser",
                "start_date": None,
                "end_date": None,
            },
            "should_search": False,
            "needs_clarification": True,
            "assistant_reply": "Konser iyi. Şehir veya tarih fark eder mi?",
        }

        normalized = events.normalize_ai_chat_intent(payload)

        self.assertEqual(normalized["intent"], "update_filters")
        self.assertEqual(normalized["filters"]["category"], "Konser")
        self.assertFalse(normalized["should_search"])
        self.assertTrue(normalized["needs_clarification"])
        self.assertEqual(normalized["assistant_reply"], "Konser iyi. Şehir veya tarih fark eder mi?")

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
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": None,
                    "category": None,
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": False,
                "needs_clarification": True,
                "assistant_reply": "Nasıl bir eğlence arıyorsun: konser, tiyatro, festival ya da spor gibi?",
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
        self.assertFalse(response["should_search"])
        self.assertEqual(response["intent"], "search_events")
        self.assertEqual(response["reply"], "Nasıl bir eğlence arıyorsun: konser, tiyatro, festival ya da spor gibi?")

    def test_ai_chat_updates_filters_without_querying_database(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="İstanbul ekle ama henüz arama")
            ],
            current_filters=events.AIChatFilters(category="Konser")
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "update_filters",
                "filters": {
                    "city": "İstanbul",
                    "category": "Konser",
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": False,
                "needs_clarification": False,
                "assistant_reply": "İstanbul'u ekledim, arama yapmıyorum.",
            }
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "update_filters")
        self.assertFalse(response["should_search"])
        self.assertEqual(response["events"], [])
        self.assertEqual(response["filters_applied"]["city"], "İstanbul")
        self.assertEqual(response["filters_applied"]["category"], "Konser")

    def test_ai_chat_blocks_single_filter_search_and_asks_next_question(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="assistant", content="Nasıl bir eğlence olsun?"),
                events.AIChatMessage(role="user", content="Konser olsun")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": None,
                    "category": "Konser",
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": True,
                "needs_clarification": False,
                "assistant_reply": "Konserleri arıyorum.",
            }
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "search_events")
        self.assertFalse(response["should_search"])
        self.assertTrue(response["needs_clarification"])
        self.assertEqual(response["events"], [])
        self.assertEqual(response["filters_applied"]["category"], "Konser")
        self.assertIn("şehir", response["reply"].lower())

    def test_ai_chat_allows_single_filter_when_user_says_anything_goes(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="assistant", content="Konser için şehir veya tarih fark eder mi?"),
                events.AIChatMessage(role="user", content="fark etmez ara")
            ],
            current_filters=events.AIChatFilters(category="Konser")
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": None,
                    "category": "Konser",
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": True,
                "needs_clarification": False,
                "assistant_reply": "Tüm konserlere bakıyorum.",
            }
            events.query_events_by_filters = lambda db, filters: [object()]

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertTrue(response["should_search"])
        self.assertEqual(len(response["events"]), 1)
        self.assertEqual(response["filters_applied"]["category"], "Konser")

    def test_ai_chat_smalltalk_does_not_turn_into_search_prompt(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="nabıyon ya")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "smalltalk",
                "filters": {
                    "city": None,
                    "category": None,
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": False,
                "needs_clarification": False,
                "assistant_reply": "Buradayım, etkinlik avına çıkmaya hazırım.",
            }
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "smalltalk")
        self.assertFalse(response["should_search"])
        self.assertFalse(response["needs_clarification"])
        self.assertEqual(response["reply"], "Buradayım, etkinlik avına çıkmaya hazırım.")

    def test_ai_chat_queries_database_when_intent_should_search(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="İstanbul'da konser ara")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": "İstanbul",
                    "category": "Konser",
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": True,
                "needs_clarification": False,
                "assistant_reply": "İstanbul'daki konserleri arıyorum.",
            }
            events.query_events_by_filters = lambda db, filters: [object(), object()]

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "search_events")
        self.assertTrue(response["should_search"])
        self.assertEqual(len(response["events"]), 2)
        self.assertEqual(response["filters_applied"]["city"], "İstanbul")

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
