import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from routers import events


class AIChatHelpersTest(unittest.TestCase):
    def test_event_id_routes_are_int_constrained_so_ai_chat_is_not_parsed_as_event_id(self):
        dynamic_event_routes = [
            route.path
            for route in events.router.routes
            if "{event_id" in route.path or "{id" in route.path
        ]

        self.assertIn("/api/events/{event_id:int}", dynamic_event_routes)
        self.assertIn("/api/events/{event_id:int}/reviews", dynamic_event_routes)
        self.assertIn("/api/events/{id:int}/calendar", dynamic_event_routes)
        for route_path in dynamic_event_routes:
            self.assertNotIn("{event_id}", route_path)
            self.assertNotIn("{id}", route_path)

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
        self.assertIn("konser", response["reply"].lower())
        self.assertEqual(response["slot_state"]["requested_slot"], "category")

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

    def test_ai_chat_blocks_city_and_category_until_date_slot_is_answered(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="istanbulda konser")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: (_ for _ in ()).throw(
                AssertionError("LLM should not be needed for common city and category phrases")
            )
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried until date is answered")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertFalse(response["should_search"])
        self.assertTrue(response["needs_clarification"])
        self.assertEqual(response["events"], [])
        self.assertEqual(response["filters_applied"]["city"], "İstanbul")
        self.assertEqual(response["filters_applied"]["category"], "Konser")
        self.assertEqual(response["slot_state"]["date"], "unknown")
        self.assertEqual(response["slot_state"]["requested_slot"], "date")
        self.assertIn("tarih", response["reply"].lower())

    def test_ai_chat_marks_requested_slot_as_any_and_asks_next_slot(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="assistant", content="Konser için hangi şehir olsun? Fark etmezse söyle."),
                events.AIChatMessage(role="user", content="fark etmez")
            ],
            current_filters=events.AIChatFilters(category="Konser"),
            slot_state=events.AIChatSlotState(
                category="filled",
                city="unknown",
                date="unknown",
                requested_slot="city",
            ),
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "update_filters",
                "filters": {
                    "city": None,
                    "category": None,
                    "start_date": None,
                    "end_date": None,
                },
                "should_search": False,
                "needs_clarification": True,
                "assistant_reply": "Tamam, şehir fark etmiyor.",
            }
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried before date slot")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertFalse(response["should_search"])
        self.assertTrue(response["needs_clarification"])
        self.assertEqual(response["slot_state"]["city"], "any")
        self.assertEqual(response["slot_state"]["requested_slot"], "date")
        self.assertIn("tarih", response["reply"].lower())

    def test_ai_chat_turns_august_first_week_reply_into_date_filters(self):
        today = events.date.today()
        expected_year = today.year if today.month <= 8 else today.year + 1
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="assistant", content="Ankara için tarih aralığı var mı, yoksa tarih fark etmez mi?"),
                events.AIChatMessage(role="user", content="var kankam agustosun ilk haftasi için bakalım")
            ],
            current_filters=events.AIChatFilters(city="Ankara"),
            slot_state=events.AIChatSlotState(
                category="any",
                city="filled",
                date="unknown",
                requested_slot="date",
            ),
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        observed_filters = {}
        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": "Ankara",
                    "category": None,
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                },
                "should_search": True,
                "needs_clarification": False,
                "assistant_reply": "Ankara için Ağustos ayına bakıyorum.",
            }

            def fake_query(db, filters):
                observed_filters.update(filters)
                return [object()]

            events.query_events_by_filters = fake_query

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertTrue(response["should_search"])
        self.assertEqual(response["slot_state"]["date"], "filled")
        self.assertEqual(response["filters_applied"]["city"], "Ankara")
        self.assertEqual(response["filters_applied"]["start_date"], f"{expected_year}-08-01")
        self.assertEqual(response["filters_applied"]["end_date"], f"{expected_year}-08-07")
        self.assertEqual(observed_filters["start_date"], f"{expected_year}-08-01")

    def test_ai_chat_turns_specific_day_month_reply_into_single_day_filter(self):
        today = events.date.today()
        expected_year = today.year if today.month <= 8 else today.year + 1
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="assistant", content="Ankara için tarih aralığı var mı, yoksa tarih fark etmez mi?"),
                events.AIChatMessage(role="user", content="ankarada 15 agustosta var mi")
            ],
            current_filters=events.AIChatFilters(city="Ankara"),
            slot_state=events.AIChatSlotState(
                category="any",
                city="filled",
                date="unknown",
                requested_slot="date",
            ),
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: {
                "intent": "search_events",
                "filters": {
                    "city": "Ankara",
                    "category": None,
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-31",
                },
                "should_search": True,
                "needs_clarification": False,
                "assistant_reply": "Ankara için Ağustos ayına bakıyorum.",
            }
            events.query_events_by_filters = lambda db, filters: []

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        expected_date = f"{expected_year}-08-15"
        self.assertTrue(response["should_search"])
        self.assertEqual(response["filters_applied"]["start_date"], expected_date)
        self.assertEqual(response["filters_applied"]["end_date"], expected_date)

    def test_ai_chat_does_not_widen_specific_day_month_to_whole_month(self):
        today = events.date.today()
        expected_year = today.year if today.month <= 7 else today.year + 1
        normalized = events.normalize_text_for_intent("20 temmuzda olan var mi spesifik olarak")

        date_range = events.detect_date_range_from_text(normalized)

        expected_date = f"{expected_year}-07-20"
        self.assertEqual(date_range, {
            "start_date": expected_date,
            "end_date": expected_date,
        })

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
        self.assertIn("Selam", response["reply"])

    def test_ai_chat_handles_greeting_without_llm_or_database(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="selam")
            ]
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: (_ for _ in ()).throw(
                AssertionError("LLM should not be called for simple greeting")
            )
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
        self.assertEqual(response["events"], [])
        self.assertIn("Selam", response["reply"])

    def test_ai_chat_resets_filters_for_delete_all_filters_phrase_without_llm(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="butun filtreleri sil")
            ],
            current_filters=events.AIChatFilters(city="Ankara", category="Konser"),
            slot_state=events.AIChatSlotState(
                category="filled",
                city="filled",
                date="unknown",
                requested_slot="date",
            ),
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: (_ for _ in ()).throw(
                AssertionError("LLM should not be called for reset")
            )
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried for reset")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "reset_filters")
        self.assertFalse(response["should_search"])
        self.assertFalse(response["needs_clarification"])
        self.assertEqual(response["filters_applied"], events.empty_event_filters())
        self.assertEqual(response["slot_state"], events.empty_slot_state())

    def test_ai_chat_meta_complaint_does_not_call_llm_or_database(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="yanit hazirla demedim")
            ],
            current_filters=events.AIChatFilters(city="Ankara"),
        )

        original_extract = events.extract_ai_chat_intent
        original_query = events.query_events_by_filters

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: (_ for _ in ()).throw(
                AssertionError("LLM should not be called for meta complaint")
            )
            events.query_events_by_filters = lambda db, filters: (_ for _ in ()).throw(
                AssertionError("Database should not be queried for meta complaint")
            )

            response = events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract
            events.query_events_by_filters = original_query

        self.assertEqual(response["intent"], "smalltalk")
        self.assertFalse(response["should_search"])
        self.assertFalse(response["needs_clarification"])
        self.assertEqual(response["filters_applied"]["city"], "Ankara")
        self.assertIn("arama yapmıyorum", response["reply"].lower())

    def test_ai_chat_queries_database_when_all_slots_are_ready(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="İstanbul'da bu hafta konser ara")
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
                    "start_date": "2026-06-29",
                    "end_date": "2026-07-05",
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
        self.assertEqual(response["slot_state"]["date"], "filled")

    def test_ai_chat_returns_controlled_http_error_when_llm_fails(self):
        request = events.AIChatRequest(
            messages=[
                events.AIChatMessage(role="user", content="açık havada güzel bir plan istiyorum")
            ]
        )

        original_extract = events.extract_ai_chat_intent

        try:
            events.extract_ai_chat_intent = lambda messages, current_filters=None: (_ for _ in ()).throw(
                TimeoutError("ollama timed out")
            )

            with self.assertRaises(events.HTTPException) as raised:
                events.ai_chat_events(request, db=object())
        finally:
            events.extract_ai_chat_intent = original_extract

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail["message"],
            "AI sohbet servisi şu anda yanıt vermiyor. Lütfen biraz sonra tekrar deneyin.",
        )
        self.assertEqual(raised.exception.detail["error_code"], "AI_CHAT_UNAVAILABLE")

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
