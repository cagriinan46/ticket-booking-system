import json
import logging
import re
import time
from datetime import date

from fastapi import HTTPException
from pydantic import BaseModel

from constants.ai import AI_CHAT_INTENTS, AI_CHAT_JSON_SCHEMA, FILTER_KEYS, SLOT_KEYS, SLOT_STATUSES
from constants.events import CATEGORY_ALIASES, KNOWN_CITIES
from services.ai_common import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    clean_ai_value,
    ollama_client,
    parse_llm_json,
)
from services.event_service import query_events_by_filters
from utils.dates import detect_date_range_from_text
from utils.text import contains_any, normalize_text_for_intent


logger = logging.getLogger(__name__)


def empty_event_filters():
    return {key: None for key in FILTER_KEYS}


def filters_to_dict(filters):
    if filters is None:
        return empty_event_filters()

    if isinstance(filters, BaseModel):
        if hasattr(filters, "model_dump"):
            data = filters.model_dump()
        else:
            data = filters.dict()
    else:
        data = dict(filters)

    return {key: clean_ai_value(data.get(key)) for key in FILTER_KEYS}


def merge_event_filters(current_filters, new_filters):
    merged = filters_to_dict(current_filters)
    incoming = filters_to_dict(new_filters)

    for key in FILTER_KEYS:
        if incoming.get(key):
            merged[key] = incoming[key]

    return merged


def empty_slot_state():
    return {
        "category": "unknown",
        "city": "unknown",
        "date": "unknown",
        "requested_slot": None,
    }


def slot_state_to_dict(slot_state):
    if slot_state is None:
        return empty_slot_state()

    if isinstance(slot_state, BaseModel):
        if hasattr(slot_state, "model_dump"):
            data = slot_state.model_dump()
        else:
            data = slot_state.dict()
    else:
        data = dict(slot_state)

    state = empty_slot_state()
    for slot in SLOT_KEYS:
        value = data.get(slot)
        if value in SLOT_STATUSES:
            state[slot] = value

    requested_slot = data.get("requested_slot")
    if requested_slot in SLOT_KEYS:
        state["requested_slot"] = requested_slot

    return state


def sync_slot_state_with_filters(filters, slot_state=None):
    state = slot_state_to_dict(slot_state)
    filters = filters_to_dict(filters)

    if filters.get("category"):
        state["category"] = "filled"
    elif state["category"] == "filled":
        state["category"] = "unknown"

    if filters.get("city"):
        state["city"] = "filled"
    elif state["city"] == "filled":
        state["city"] = "unknown"

    if filters.get("start_date") or filters.get("end_date"):
        state["date"] = "filled"
    elif state["date"] == "filled":
        state["date"] = "unknown"

    if state.get("requested_slot") and state[state["requested_slot"]] != "unknown":
        state["requested_slot"] = None

    return state


def latest_user_message(messages):
    for message in reversed(messages):
        if message.role == "user":
            return message.content.strip()
    return ""


def infer_requested_slot_from_messages(messages):
    for message in reversed(messages):
        if message.role != "assistant":
            continue

        content = normalize_text_for_intent(message.content)
        if "tarih" in content or "zaman" in content or "hafta" in content:
            return "date"
        if "sehir" in content or "nerede" in content or "istanbul" in content:
            return "city"
        if "kategori" in content or "tur" in content or "etkinlik" in content or "atmosfer" in content:
            return "category"

    return None


def user_accepts_any_for_slot(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    any_phrases = [
        "fark etmez",
        "farketmez",
        "onemli degil",
        "önemli değil",
        "herhangi",
        "hepsi",
        "tumu",
        "tümü",
        "bos gec",
        "boş geç",
    ]
    if not any(phrase in latest for phrase in any_phrases):
        return None

    if "sehir" in latest or "neresi" in latest or "nerede" in latest:
        return "city"
    if "tarih" in latest or "zaman" in latest or "gun" in latest or "gün" in latest:
        return "date"
    if "kategori" in latest or "tur" in latest or "tür" in latest:
        return "category"

    return "requested"


def apply_any_answer_to_slot_state(messages, slot_state):
    state = slot_state_to_dict(slot_state)
    accepted_slot = user_accepts_any_for_slot(messages)
    if not accepted_slot:
        return state

    if accepted_slot == "requested":
        accepted_slot = state.get("requested_slot") or infer_requested_slot_from_messages(messages)

    if accepted_slot in SLOT_KEYS:
        state[accepted_slot] = "any"
        state["requested_slot"] = None

    return state


def next_unknown_slot(slot_state):
    state = slot_state_to_dict(slot_state)
    for slot in SLOT_KEYS:
        if state[slot] == "unknown":
            return slot
    return None


def slot_state_is_ready(slot_state):
    state = slot_state_to_dict(slot_state)
    return all(state[slot] in ["filled", "any"] for slot in SLOT_KEYS)


def is_reset_request(normalized_text):
    reset_action = contains_any(normalized_text, ["temizle", "sil", "sifirla"])
    reset_scope = contains_any(normalized_text, ["filtre", "arama", "hepsi", "her sey"])
    return (
        (reset_action and reset_scope)
        or normalized_text in ["temizle", "sifirla"]
        or "bastan basla" in normalized_text
    )


def is_meta_stop_request(normalized_text):
    if normalized_text in ["bekle", "dur"]:
        return True

    if "demedim" in normalized_text and contains_any(normalized_text, ["yanit", "cevap", "hazirla", "arama", "ara"]):
        return True

    return "arama" in normalized_text and contains_any(normalized_text, ["yapma", "etme"])


def is_broaden_request(normalized_text):
    return contains_any(
        normalized_text,
        [
            "genislet",
            "genisletelim",
            "genisletebiliriz",
            "daha genis",
            "daha geniş",
            "filtreleri genis",
            "filtreleri geniş",
        ],
    )


def build_broaden_intent(current_filters):
    filters = filters_to_dict(current_filters)
    broadened_slot = None
    reply = "Aramayı genişletiyorum."

    if filters.get("start_date") or filters.get("end_date"):
        filters["start_date"] = None
        filters["end_date"] = None
        broadened_slot = "date"
        reply = "Tarih filtresini kaldırıp daha geniş bakıyorum."
    elif filters.get("category"):
        filters["category"] = None
        broadened_slot = "category"
        reply = "Kategori filtresini kaldırıp daha geniş bakıyorum."
    elif filters.get("city"):
        filters["city"] = None
        broadened_slot = "city"
        reply = "Şehir filtresini kaldırıp daha geniş bakıyorum."
    else:
        reply = "Filtre yok, tüm etkinliklere genel bakıyorum."

    return {
        "intent": "search_events",
        "filters": filters,
        "should_search": True,
        "needs_clarification": False,
        "assistant_reply": reply,
        "broadening_slot": broadened_slot,
    }


def user_requested_no_search(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    if latest in ["arama", "search etme", "dont search", "don't search"]:
        return True

    return contains_any(latest, ["arama", "search"]) and contains_any(latest, ["yapma", "etme", "henuz", "henüz", "simdi", "şimdi"])


def user_explicitly_requests_search_anyway(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    wants_search = bool(re.search(r"\bara\b", latest)) or contains_any(latest, ["arama", "bakalim", "bakalım"])
    broad_scope = contains_any(latest, ["direkt", "gitsin", "genel", "genis", "geniş", "hepsi", "tumu", "tümü", "fark etmez", "farketmez", "bu filtre"])
    return wants_search and broad_scope


def build_slot_follow_up_question(filters, slot_state):
    missing_slot = next_unknown_slot(slot_state)
    category = filters.get("category")
    city = filters.get("city")

    if missing_slot == "category":
        return "Ne tür bir etkinlik olsun: konser, tiyatro, festival, stand-up ya da spor? Fark etmezse kategori seçmeden ilerleyebilirim."

    if missing_slot == "city":
        if category:
            return f"{category} için hangi şehir olsun? Fark etmezse şehir filtresini boş geçebilirim."
        return "Hangi şehirde bakalım? Fark etmezse şehir filtresini boş geçebilirim."

    if missing_slot == "date":
        if city and category:
            return f"{city} için {category} aramasında tarih aralığı var mı, yoksa tarih fark etmez mi?"
        if category:
            return f"{category} için tarih aralığı var mı, yoksa tarih fark etmez mi?"
        if city:
            return f"{city} için tarih aralığı var mı, yoksa tarih fark etmez mi?"
        return "Tarih aralığı var mı, yoksa tarih fark etmez mi?"

    return "Tamam, bu bilgilerle arama yapabilirim."


def detect_category_from_text(normalized_text):
    for alias, category in CATEGORY_ALIASES.items():
        if normalize_text_for_intent(alias) in normalized_text:
            return category
    return None


def detect_city_from_text(normalized_text):
    for city in KNOWN_CITIES:
        if normalize_text_for_intent(city) in normalized_text:
            return city
    return None


def apply_date_override_from_latest_message(intent, messages):
    date_range = detect_date_range_from_text(
        normalize_text_for_intent(latest_user_message(messages))
    )
    if not date_range:
        return intent

    filters = filters_to_dict(intent.get("filters"))
    filters["start_date"] = date_range["start_date"]
    filters["end_date"] = date_range["end_date"]
    intent["filters"] = filters

    return intent


def quick_filter_intent_from_message(messages, current_filters=None):
    latest = normalize_text_for_intent(latest_user_message(messages))
    if not latest:
        return None

    category = detect_category_from_text(latest)
    city = detect_city_from_text(latest)
    date_range = detect_date_range_from_text(latest)
    vague_search = contains_any(
        latest,
        [
            "eglenceli",
            "eğlenceli",
            "bir seyler",
            "bir şeyler",
            "ne var",
            "oner",
            "öner",
            "etkinlik bak",
            "etkinlik ara",
        ],
    )

    if not category and not city and not date_range and not vague_search:
        return None

    filters = empty_event_filters()
    filters["category"] = category
    filters["city"] = city
    if date_range:
        filters["start_date"] = date_range["start_date"]
        filters["end_date"] = date_range["end_date"]

    intent = "update_filters" if user_requested_no_search(messages) else "search_events"
    assistant_reply = "Filtreleri aldım, kalan bilgileri netleştirelim."
    if city and category and date_range:
        assistant_reply = f"{city}, {category} ve tarih aralığını aldım."
    elif city and category:
        assistant_reply = f"{city} ve {category} bilgisini aldım."
    elif city and date_range:
        assistant_reply = f"{city} ve tarih aralığını aldım."
    elif category and date_range:
        assistant_reply = f"{category} ve tarih aralığını aldım."
    elif category:
        assistant_reply = f"{category} bilgisini aldım."
    elif city:
        assistant_reply = f"{city} bilgisini aldım."
    elif date_range:
        assistant_reply = "Tarih aralığını aldım."

    return normalize_ai_chat_intent(
        {
            "intent": intent,
            "filters": filters,
            "should_search": intent == "search_events",
            "needs_clarification": True,
            "assistant_reply": assistant_reply,
        },
        current_filters,
    )


def build_llm_failure_fallback_intent(current_filters, current_slot_state):
    return {
        "intent": "help",
        "filters": filters_to_dict(current_filters),
        "should_search": False,
        "needs_clarification": True,
        "assistant_reply": "AI yorumlama servisi şu an yavaşladı; şehir, tarih veya kategori bilgisini daha net yazarsan devam edebilirim.",
        "slot_state": slot_state_to_dict(current_slot_state),
    }


def enforce_slot_filling(intent, messages, current_slot_state=None):
    if intent.get("intent") == "reset_filters":
        intent["slot_state"] = empty_slot_state()
        intent["should_search"] = False
        intent["needs_clarification"] = False
        return intent

    filters = filters_to_dict(intent.get("filters"))
    slot_state = sync_slot_state_with_filters(filters, current_slot_state)
    slot_state = apply_any_answer_to_slot_state(messages, slot_state)
    slot_state = sync_slot_state_with_filters(filters, slot_state)

    broadening_slot = intent.get("broadening_slot")
    if broadening_slot in SLOT_KEYS:
        slot_state[broadening_slot] = "any"

    if intent.get("intent") in ["smalltalk", "help"]:
        intent["slot_state"] = slot_state
        intent["should_search"] = False
        intent["needs_clarification"] = False
        return intent

    explicit_search_anyway = user_explicitly_requests_search_anyway(messages)
    no_search_requested = user_requested_no_search(messages)
    ready_to_search = slot_state_is_ready(slot_state)
    missing_slot = next_unknown_slot(slot_state)

    intent["filters"] = filters
    intent["slot_state"] = slot_state

    if no_search_requested:
        intent["should_search"] = False
        intent["needs_clarification"] = False
        slot_state["requested_slot"] = missing_slot
        intent["assistant_reply"] = intent.get("assistant_reply") or "Tamam, filtreleri güncelledim ama arama yapmıyorum."
        return intent

    if ready_to_search or explicit_search_anyway:
        intent["intent"] = "search_events"
        intent["should_search"] = True
        intent["needs_clarification"] = False
        slot_state["requested_slot"] = None
        if not intent.get("assistant_reply"):
            intent["assistant_reply"] = "Tamam, bu bilgilerle etkinliklere bakıyorum."
        return intent

    if missing_slot:
        intent["should_search"] = False
        intent["needs_clarification"] = True
        slot_state["requested_slot"] = missing_slot
        intent["assistant_reply"] = build_slot_follow_up_question(filters, slot_state)

    return intent


def prehandle_ai_chat_intent(messages, current_filters=None):
    latest = normalize_text_for_intent(latest_user_message(messages))
    filters = filters_to_dict(current_filters)

    if not latest:
        return None

    if is_reset_request(latest):
        return {
            "intent": "reset_filters",
            "filters": empty_event_filters(),
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Filtreleri temizledim. Baştan başlayabiliriz.",
        }

    if is_meta_stop_request(latest):
        return {
            "intent": "smalltalk",
            "filters": filters,
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Tamam, arama yapmıyorum. İstersen filtreleri temizleyebilir veya yeni kriterleri yazabilirsin.",
        }

    if is_broaden_request(latest):
        return build_broaden_intent(filters)

    help_phrases = ["yardim", "nasil kullan", "ne yapabilirsin", "komut"]
    if any(phrase in latest for phrase in help_phrases):
        return {
            "intent": "help",
            "filters": filters,
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Bana etkinlik türü, şehir veya tarih söyleyebilirsin. Eksik kalanları sırayla sorarım; 'fark etmez' dersen o filtreyi boş geçerim.",
        }

    if user_accepts_any_for_slot(messages):
        should_search = user_explicitly_requests_search_anyway(messages)
        return {
            "intent": "search_events" if should_search else "update_filters",
            "filters": filters,
            "should_search": should_search,
            "needs_clarification": not should_search,
            "assistant_reply": "Tamam, o alanı boş geçiyorum.",
        }

    smalltalk_exact = [
        "selam",
        "merhaba",
        "sa",
        "naber",
        "nabiyon",
        "nabiyosun",
        "napiyon",
        "napiyosun",
        "ne yapiyon",
        "ne yapiyosun",
        "nasilsin",
        "tesekkurler",
        "tesekkur ederim",
    ]
    search_words = ["konser", "tiyatro", "festival", "stand", "spor", "etkinlik", "bilet", "ara", "istanbul", "ankara", "izmir"]

    if latest in smalltalk_exact or (
        any(phrase in latest for phrase in smalltalk_exact)
        and not any(word in latest for word in search_words)
    ):
        return {
            "intent": "smalltalk",
            "filters": filters,
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Selam, buradayım. Etkinlik bakmak istersen tür, şehir veya tarih söyleyebilirsin.",
        }

    return None


def user_allows_broad_search(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    broad_phrases = [
        "fark etmez",
        "farketmez",
        "önemli değil",
        "onemli degil",
        "herhangi",
        "hepsi",
        "tümü",
        "tumu",
        "genel",
        "direkt ara",
        "ara gitsin",
    ]

    return any(phrase in latest for phrase in broad_phrases)


def active_filter_count(filters):
    return sum(1 for key in FILTER_KEYS if filters.get(key))


def build_missing_filter_question(filters):
    category = filters.get("category")
    city = filters.get("city")
    has_date = bool(filters.get("start_date") or filters.get("end_date"))

    if category and not city and not has_date:
        return f"{category} için şehir veya tarih fark eder mi? İstersen 'fark etmez' deyip tüm uygun etkinliklere bakmamı söyleyebilirsin."

    if city and not category and not has_date:
        return f"{city} için hangi tür etkinlik olsun: konser, tiyatro, festival, stand-up ya da spor? Tarih fark etmiyorsa onu da söyleyebilirsin."

    if has_date and not city and not category:
        return "Bu tarih aralığında hangi şehir veya etkinlik türü ilgini çeker? Fark etmezse geniş arayabilirim."

    return "Aramayı daraltmak için şehir, tarih veya kategori bilgisi ekleyebilir misin? Fark etmezse bunu söylemen yeterli."


def enforce_search_readiness(intent, messages):
    if intent.get("intent") != "search_events" or not intent.get("should_search"):
        return intent

    filters = intent.get("filters", empty_event_filters())
    count = active_filter_count(filters)

    if count == 0:
        intent["should_search"] = False
        intent["needs_clarification"] = True
        intent["assistant_reply"] = "Ne aradığını biraz açalım mı? Şehir, tarih veya etkinlik türünden biriyle başlayabiliriz."
        return intent

    if count == 1 and not user_allows_broad_search(messages):
        intent["should_search"] = False
        intent["needs_clarification"] = True
        intent["assistant_reply"] = build_missing_filter_question(filters)

    return intent


def normalize_ai_chat_intent(payload, current_filters=None):
    intent = clean_ai_value(payload.get("intent")) or "search_events"
    if intent not in AI_CHAT_INTENTS:
        intent = "search_events"

    assistant_reply = clean_ai_value(payload.get("assistant_reply"))
    needs_clarification = bool(payload.get("needs_clarification", False))
    should_search = bool(payload.get("should_search", False))

    if intent == "reset_filters":
        filters = empty_event_filters()
        should_search = False
        needs_clarification = False
        assistant_reply = assistant_reply or "Filtreleri temizledim. Yeni bir arama için şehir, tarih veya kategori yazabilirsin."
    elif intent in ["smalltalk", "help"]:
        filters = filters_to_dict(current_filters)
        should_search = False
        needs_clarification = False
        if not assistant_reply:
            if intent == "help":
                assistant_reply = "Şehir, tarih veya kategori söyleyerek etkinlik arayabilirsin. İstersen filtreleri güncelleyebilir veya temizleyebilirsin."
            else:
                assistant_reply = "Buradayım. Etkinlik aramak istersen şehir, tarih veya kategori söylemen yeterli."
    elif intent == "update_filters":
        filters = merge_event_filters(current_filters, payload.get("filters"))
        should_search = False
        assistant_reply = assistant_reply or "Filtreleri güncelledim. Hazır olduğunda arama yapmamı söyleyebilirsin."
    else:
        filters = merge_event_filters(current_filters, payload.get("filters"))
        has_filter = any(filters[key] for key in FILTER_KEYS)
        should_search = should_search and has_filter and not needs_clarification

        if not has_filter and not needs_clarification:
            needs_clarification = True

        if needs_clarification:
            should_search = False
            assistant_reply = assistant_reply or "Ne tarz bir etkinlik düşünüyorsun? Şehir, tarih veya kategoriyle daraltabilirim."
        else:
            assistant_reply = assistant_reply or "Uygun etkinlikleri arıyorum."

    return {
        "intent": intent,
        "filters": filters,
        "should_search": should_search,
        "needs_clarification": needs_clarification,
        "assistant_reply": assistant_reply,
    }


def describe_filters(intent):
    parts = []

    if intent.get("city"):
        parts.append(intent["city"])

    if intent.get("category"):
        parts.append(intent["category"])

    if intent.get("start_date") and intent.get("end_date"):
        if intent["start_date"] == intent["end_date"]:
            parts.append(intent["start_date"])
        else:
            parts.append(f"{intent['start_date']} - {intent['end_date']}")
    elif intent.get("start_date"):
        parts.append(f"{intent['start_date']} sonrası")
    elif intent.get("end_date"):
        parts.append(f"{intent['end_date']} öncesi")

    return ", ".join(parts)


def build_ai_chat_reply(events, intent):
    if "assistant_reply" in intent and not intent.get("should_search"):
        return intent.get("assistant_reply")

    if intent.get("needs_clarification"):
        return intent.get("follow_up_question") or intent.get("assistant_reply")

    filters = intent.get("filters") if "filters" in intent else intent
    filter_text = describe_filters(filters)

    if events:
        if filter_text:
            return f"{filter_text} kriterleriyle {len(events)} etkinlik buldum."
        return f"Aramana uygun {len(events)} etkinlik buldum."

    if filter_text:
        return f"{filter_text} kriterlerine uygun etkinlik bulamadım. Farklı bir şehir, tarih veya kategori deneyebilirsiniz."

    return "Aramana uygun etkinlik bulamadım. Şehir, tarih veya kategori ekleyerek tekrar deneyebilirsiniz."


def build_ai_chat_search_reply(events, intent):
    filter_text = describe_filters(intent.get("filters", {}))

    if events:
        if filter_text:
            return f"{filter_text} için {len(events)} etkinlik buldum."
        return f"Aramana uygun {len(events)} etkinlik buldum."

    if filter_text:
        return f"{filter_text} kriterlerine uygun etkinlik bulamadım. İstersen filtreleri genişletebiliriz."

    return "Bu aramaya uygun etkinlik bulamadım. İstersen şehir, tarih veya kategoriyle yeniden deneyebiliriz."


def extract_ai_chat_intent(messages, current_filters=None):
    today = date.today().isoformat()
    active_filters = filters_to_dict(current_filters)

    system_prompt = f"""
        Sen PortaBilet için çalışan intent çıkarma katmanısın.
        Bugünün tarihi: {today}.
        Mevcut filtreler: {json.dumps(active_filters, ensure_ascii=False)}.

        Veritabanını sorgulama ve etkinlik uydurma. Sadece JSON dön.
        JSON alanları: intent, filters, should_search, needs_clarification, assistant_reply.

        intent değerleri: search_events, update_filters, reset_filters, smalltalk, help.
        filters yalnızca city, category, start_date, end_date içermeli.
        category yalnızca Konser, Tiyatro, Festival, Stand-up, Spor veya null olabilir.

        Kullanıcının açıkça söylediği yeni filtreleri yaz; söylemediği alanları null bırak.
        Tarihten eminsen YYYY-MM-DD kullan, emin değilsen null bırak.
        Selam/teşekkür gibi sohbetlerde smalltalk dön.
        Yardım sorularında help dön.
        Filtre temizleme isteğinde reset_filters dön.
        Arama yapılmasını istemiyorsa should_search false dön.

        Sadece geçerli JSON dön. Açıklama veya Markdown yazma.
        """

    ollama_messages = [{"role": "system", "content": system_prompt}]
    ollama_messages.extend(
        {"role": message.role, "content": message.content.strip()}
        for message in messages
        if message.content.strip()
    )

    logger.info(
        "AI chat Ollama call starting: model=%s host=%s timeout=%ss message_count=%s",
        OLLAMA_MODEL,
        OLLAMA_HOST,
        OLLAMA_TIMEOUT_SECONDS,
        len(ollama_messages),
    )
    started_at = time.monotonic()

    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=ollama_messages,
            stream=False,
            format=AI_CHAT_JSON_SCHEMA,
            options={
                "temperature": 0
            }
        )
    except Exception:
        logger.exception(
            "AI chat Ollama call failed after %.2fs",
            time.monotonic() - started_at,
        )
        raise

    logger.info(
        "AI chat Ollama call finished in %.2fs",
        time.monotonic() - started_at,
    )

    llm_output = response["message"]["content"].strip()
    return normalize_ai_chat_intent(parse_llm_json(llm_output), active_filters)


def handle_ai_chat_events(request, db):
    if not request.messages or not any(message.content.strip() for message in request.messages):
        raise HTTPException(
            status_code=400,
            detail="Lütfen aramak istediğiniz etkinliği yazın."
        )

    current_filters = filters_to_dict(request.current_filters)
    current_slot_state = sync_slot_state_with_filters(
        current_filters,
        request.slot_state,
    )
    latest_message = latest_user_message(request.messages)

    logger.info(
        "AI chat request received: latest=%r current_filters=%s slot_state=%s",
        latest_message,
        current_filters,
        current_slot_state,
    )

    prehandled_intent = prehandle_ai_chat_intent(request.messages, current_filters)

    if prehandled_intent:
        intent = enforce_slot_filling(
            prehandled_intent,
            request.messages,
            current_slot_state,
        )
        logger.info(
            "AI chat prehandled intent resolved: intent=%s should_search=%s needs_clarification=%s slot_state=%s",
            intent["intent"],
            intent["should_search"],
            intent["needs_clarification"],
            intent["slot_state"],
        )
    else:
        quick_intent = quick_filter_intent_from_message(request.messages, current_filters)
        if quick_intent:
            intent = enforce_slot_filling(
                quick_intent,
                request.messages,
                current_slot_state,
            )
            logger.info(
                "AI chat quick intent handled: intent=%s should_search=%s needs_clarification=%s filters=%s slot_state=%s",
                intent["intent"],
                intent["should_search"],
                intent["needs_clarification"],
                intent["filters"],
                intent["slot_state"],
            )
        else:
            logger.info("AI chat falling back to LLM extraction")
            try:
                intent = extract_ai_chat_intent(request.messages, current_filters)
                intent = apply_date_override_from_latest_message(intent, request.messages)
                intent = enforce_slot_filling(intent, request.messages, current_slot_state)
            except Exception:
                logger.exception("AI chat analysis failed before response")
                intent = build_llm_failure_fallback_intent(
                    current_filters,
                    current_slot_state,
                )

    filters = intent["filters"]

    if intent.get("needs_clarification") or not intent.get("should_search"):
        logger.info(
            "AI chat clarification/no-search response returning: intent=%s should_search=%s needs_clarification=%s filters=%s slot_state=%s",
            intent["intent"],
            intent["should_search"],
            intent["needs_clarification"],
            filters,
            intent["slot_state"],
        )
        return {
            "reply": build_ai_chat_reply([], intent),
            "intent": intent["intent"],
            "filters_applied": filters,
            "events": [],
            "should_search": False,
            "needs_clarification": intent["needs_clarification"],
            "slot_state": intent["slot_state"],
        }

    logger.info("AI chat DB query starting: filters=%s", filters)
    events = query_events_by_filters(db, filters)
    logger.info("AI chat DB query finished: count=%s", len(events))

    logger.info(
        "AI chat search response returning: intent=%s should_search=True needs_clarification=False filters=%s slot_state=%s event_count=%s",
        intent["intent"],
        filters,
        intent["slot_state"],
        len(events),
    )
    return {
        "reply": build_ai_chat_search_reply(events, intent),
        "intent": intent["intent"],
        "filters_applied": filters,
        "events": events,
        "should_search": True,
        "needs_clarification": False,
        "slot_state": intent["slot_state"],
    }
