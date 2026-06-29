from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from fastapi import HTTPException
from dotenv import load_dotenv
from typing import Literal, Optional
from sqlalchemy import text
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from datetime import date
from ollama import Client
import models
import iyzipay
import boto3
import calendar as calendar_module
import json
import logging
import os
import requests
import ollama
import time

load_dotenv()

sqs = boto3.client('sqs', region_name='eu-central-1')
SQS_QUEUE_URL = os.getenv("SQS_URL")

router = APIRouter(
    prefix="/api/events",
    tags=["Events"]
)

class AISearchRequest(BaseModel):
    prompt: str

class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AIChatFilters(BaseModel):
    city: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AIChatSlotState(BaseModel):
    category: Literal["unknown", "filled", "any"] = "unknown"
    city: Literal["unknown", "filled", "any"] = "unknown"
    date: Literal["unknown", "filled", "any"] = "unknown"
    requested_slot: Optional[Literal["category", "city", "date"]] = None

class AIChatRequest(BaseModel):
    messages: list[AIChatMessage]
    current_filters: Optional[AIChatFilters] = None
    slot_state: Optional[AIChatSlotState] = None

class EventCreate(BaseModel):
    title: str
    date: str
    location: str
    price: str
    description: str
    image: Optional[str] = None
    city: str
    category: str
    capacity: int
    time: str

class EventSchema(BaseModel):
    id: int
    title: str
    date: str
    location: str
    price: str
    description: str
    image: Optional[str] = None
    city: str
    category: str
    capacity: int
    available_tickets: int
    time: str

    class Config:
        from_attributes = True

class TicketTransferSchema(BaseModel):
    id: int
    target_email: str

class TicketResponse(BaseModel):
    id: int
    user_id: int
    event_id: int

    event: EventSchema

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    cardHolderName: str
    cardNumber: str
    expireMonth: str
    expireYear: str
    cvc: str

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="a score between 1 and 5")
    comment: Optional[str] = None

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
try:
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", os.getenv("OLLAMA_TIMEOUT", "180")))
except ValueError:
    OLLAMA_TIMEOUT_SECONDS = 15.0

logger = logging.getLogger(__name__)

ollama_client = Client(
    host=OLLAMA_HOST,
    timeout=OLLAMA_TIMEOUT_SECONDS
)

FILTER_KEYS = ["city", "category", "start_date", "end_date"]
SLOT_KEYS = ["category", "city", "date"]
SLOT_STATUSES = ["unknown", "filled", "any"]
AI_CHAT_INTENTS = ["search_events", "update_filters", "reset_filters", "smalltalk", "help"]
INVALID_AI_VALUES = ["null", "", "yok", "belirtilmemiş", "belirtilmemis", "none"]
CATEGORY_ALIASES = {
    "konser": "Konser",
    "muzik": "Konser",
    "müzik": "Konser",
    "tiyatro": "Tiyatro",
    "festival": "Festival",
    "stand-up": "Stand-up",
    "standup": "Stand-up",
    "komedi": "Stand-up",
    "spor": "Spor",
    "mac": "Spor",
    "maç": "Spor",
}
MONTH_ALIASES = {
    "ocak": 1,
    "subat": 2,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayis": 5,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "agustos": 8,
    "ağustos": 8,
    "eylul": 9,
    "eylül": 9,
    "ekim": 10,
    "kasim": 11,
    "kasım": 11,
    "aralik": 12,
    "aralık": 12,
}
KNOWN_CITIES = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya",
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır",
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep",
    "Giresun", "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul",
    "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir",
    "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş",
    "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya",
    "Samsun", "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon",
    "Tunceli", "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray",
    "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan",
    "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce",
]

AI_FILTER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "city": {
            "type": ["string", "null"]
        },
        "category": {
            "type": ["string", "null"],
            "enum": ["Konser", "Tiyatro", "Festival", "Stand-up", "Spor", None]
        },
        "start_date": {
            "type": ["string", "null"]
        },
        "end_date": {
            "type": ["string", "null"]
        }
    },
    "required": ["city", "category", "start_date", "end_date"]
}

AI_CHAT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": AI_CHAT_INTENTS
        },
        "filters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": ["string", "null"]
                },
                "category": {
                    "type": ["string", "null"],
                    "enum": ["Konser", "Tiyatro", "Festival", "Stand-up", "Spor", None]
                },
                "start_date": {
                    "type": ["string", "null"]
                },
                "end_date": {
                    "type": ["string", "null"]
                }
            },
            "required": ["city", "category", "start_date", "end_date"]
        },
        "should_search": {
            "type": "boolean"
        },
        "needs_clarification": {
            "type": "boolean"
        },
        "assistant_reply": {
            "type": "string"
        }
    },
    "required": [
        "intent",
        "filters",
        "should_search",
        "needs_clarification",
        "assistant_reply"
    ]
}

def clean_ai_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.lower() in INVALID_AI_VALUES:
            return None
        return cleaned

    return value

def normalize_ai_intent(payload):
    normalized = {
        "city": clean_ai_value(payload.get("city")),
        "category": clean_ai_value(payload.get("category")),
        "start_date": clean_ai_value(payload.get("start_date")),
        "end_date": clean_ai_value(payload.get("end_date")),
        "needs_clarification": bool(payload.get("needs_clarification", False)),
        "follow_up_question": clean_ai_value(payload.get("follow_up_question")),
    }

    has_filter = any(normalized[key] for key in FILTER_KEYS)

    if not has_filter and not normalized["needs_clarification"]:
        normalized["needs_clarification"] = True
        normalized["follow_up_question"] = "Hangi şehir, tarih veya kategoriye göre etkinlik arayayım?"

    if normalized["needs_clarification"] and not normalized["follow_up_question"]:
        normalized["follow_up_question"] = "Biraz daha detay verebilir misiniz? Şehir, tarih veya kategori söyleyebilirsiniz."

    return normalized

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

def user_requested_no_search(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    if latest in ["arama", "search etme", "dont search", "don't search"]:
        return True

    no_search_phrases = [
        "arama yapma",
        "henuz arama",
        "henüz arama",
        "simdi arama",
        "şimdi arama",
        "search etme",
        "dont search",
        "don't search",
    ]
    return any(phrase in latest for phrase in no_search_phrases)

def user_explicitly_requests_search_anyway(messages):
    latest = normalize_text_for_intent(latest_user_message(messages))
    explicit_phrases = [
        "direkt ara",
        "ara gitsin",
        "boyle ara",
        "böyle ara",
        "bu filtrelerle ara",
        "genel ara",
        "genis ara",
        "geniş ara",
        "hepsini ara",
        "tumunu ara",
        "tümünü ara",
        "fark etmez ara",
        "farketmez ara",
    ]
    return any(phrase in latest for phrase in explicit_phrases)

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

def year_for_month(month, today=None):
    today = today or date.today()
    if today.month <= month:
        return today.year
    return today.year + 1

def month_date_range(month, week_number=None, today=None):
    year = year_for_month(month, today)
    last_day = calendar_module.monthrange(year, month)[1]

    if week_number:
        start_day = min(1 + ((week_number - 1) * 7), last_day)
        end_day = min(start_day + 6, last_day)
    else:
        start_day = 1
        end_day = last_day

    return {
        "start_date": date(year, month, start_day).isoformat(),
        "end_date": date(year, month, end_day).isoformat(),
    }

def detect_week_number_from_text(normalized_text):
    week_phrases = [
        (1, ["ilk hafta", "birinci hafta", "1. hafta", "1 hafta"]),
        (2, ["ikinci hafta", "2. hafta"]),
        (3, ["ucuncu hafta", "üçüncü hafta", "3. hafta"]),
        (4, ["dorduncu hafta", "dördüncü hafta", "4. hafta", "son hafta"]),
    ]

    for week_number, phrases in week_phrases:
        if any(normalize_text_for_intent(phrase) in normalized_text for phrase in phrases):
            return week_number

    return None

def detect_date_range_from_text(normalized_text):
    today = date.today()

    if "bugun" in normalized_text or "bugün" in normalized_text:
        return {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
        }

    if "yarin" in normalized_text or "yarın" in normalized_text:
        tomorrow = today + timedelta(days=1)
        return {
            "start_date": tomorrow.isoformat(),
            "end_date": tomorrow.isoformat(),
        }

    if "gelecek hafta" in normalized_text:
        start = today + timedelta(days=7)
        end = start + timedelta(days=6)
        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

    if "bu hafta" in normalized_text or "hafta sonu" in normalized_text or "haftasonu" in normalized_text:
        end = today + timedelta(days=6)
        return {
            "start_date": today.isoformat(),
            "end_date": end.isoformat(),
        }

    week_number = detect_week_number_from_text(normalized_text)
    for month_name, month_number in MONTH_ALIASES.items():
        if normalize_text_for_intent(month_name) in normalized_text:
            return month_date_range(month_number, week_number)

    return None

def latest_message_has_date_hint(normalized_text):
    date_words = [
        "bugun", "bugün", "yarin", "yarın", "hafta", "haftasonu", "hafta sonu",
        "bu ay", "gelecek ay", "pazartesi", "sali", "salı",
        "carsamba", "çarşamba", "persembe", "perşembe", "cuma", "cumartesi",
        "pazar",
    ]
    month_words = [normalize_text_for_intent(month_name) for month_name in MONTH_ALIASES]
    return any(word in normalized_text for word in date_words + month_words)

def quick_filter_intent_from_message(messages, current_filters=None):
    latest_original = latest_user_message(messages)
    latest = normalize_text_for_intent(latest_original)
    filters = empty_event_filters()

    if not latest:
        return None

    category = detect_category_from_text(latest)
    city = detect_city_from_text(latest)
    date_range = detect_date_range_from_text(latest)
    has_date_hint = latest_message_has_date_hint(latest)
    vague_search = any(
        phrase in latest
        for phrase in [
            "eglenceli",
            "eğlenceli",
            "bir seyler",
            "bir şeyler",
            "ne var",
            "oner",
            "öner",
            "etkinlik bak",
            "etkinlik ara",
        ]
    )

    if has_date_hint and not date_range and not category and not city and not vague_search:
        return None

    if not category and not city and not date_range and not vague_search:
        return None

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

def latest_user_message(messages):
    for message in reversed(messages):
        if message.role == "user":
            return message.content.strip()
    return ""

def normalize_text_for_intent(text):
    return (
        text.lower()
        .replace("i̇", "i")
        .replace("\u0307", "")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )

def prehandle_ai_chat_intent(messages, current_filters=None):
    latest = normalize_text_for_intent(latest_user_message(messages))
    filters = filters_to_dict(current_filters)

    if not latest:
        return None

    reset_phrases = [
        "filtreleri temizle",
        "filtreleri sil",
        "butun filtreleri sil",
        "tum filtreleri sil",
        "hepsini sil",
        "sifirla",
        "bastan basla",
        "temizle",
    ]
    if any(phrase in latest for phrase in reset_phrases):
        return {
            "intent": "reset_filters",
            "filters": empty_event_filters(),
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Filtreleri temizledim. Baştan başlayabiliriz.",
        }

    meta_stop_phrases = [
        "yanit hazirla demedim",
        "cevap hazirla demedim",
        "arama demedim",
        "arama yap demedim",
        "arama yapma",
        "bekle",
        "dur",
    ]
    if any(phrase in latest for phrase in meta_stop_phrases):
        return {
            "intent": "smalltalk",
            "filters": filters,
            "should_search": False,
            "needs_clarification": False,
            "assistant_reply": "Tamam, arama yapmıyorum. İstersen filtreleri temizleyebilir veya yeni kriterleri yazabilirsin.",
        }

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

def event_filters_from_intent(intent):
    if "filters" in intent:
        return {key: intent["filters"].get(key) for key in FILTER_KEYS}

    return {key: intent.get(key) for key in FILTER_KEYS}

def parse_llm_json(content):
    cleaned = content.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start:end + 1])

def attach_available_tickets(db, events):
    for event in events:
        sold_count = db.query(models.Ticket).filter(
            models.Ticket.event_id == event.id
        ).count()
        event.available_tickets = event.capacity - sold_count

def query_events_by_filters(db, filters):
    query = db.query(models.Event)

    city = filters.get("city")
    category = filters.get("category")
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")

    if city:
        query = query.filter(models.Event.city.ilike(f"%{city}%"))

    if category:
        query = query.filter(models.Event.category.ilike(f"%{category}%"))

    if start_date:
        query = query.filter(models.Event.date >= start_date)

    if end_date:
        query = query.filter(models.Event.date <= end_date)

    events = query.all()
    attach_available_tickets(db, events)

    return events

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

def extract_ai_search_intent(prompt):
    today = date.today().isoformat()

    system_prompt = f"""
        Sen bir etkinlik arama filtresi çıkaran API'sin.
        Bugünün tarihi: {today}.

        Kullanıcı mesajından sadece şu JSON alanlarını çıkar:
        city, category, start_date, end_date.

        Kurallar:
        - Kullanıcı bir alanı açıkça belirtmediyse o alan null olmalı.
        - Genel ifadeler kategori değildir. Örneğin "herhangi bir etkinlik", "etkinlik var mı", "ne var", "bir şey var mı" ifadelerinde category null olmalı.
        - category sadece şu değerlerden biri olabilir: Konser, Tiyatro, Festival, Stand-up, Spor.
        - Kullanıcı açıkça kategori belirtirse category bu değerlerden biri olmalı. Belirtmezse category null olmalı.
        - Kullanıcı şehir belirtirse city şehir adı olmalı. Belirtmezse city null olmalı.
        - Tarih varsa start_date ve end_date YYYY-MM-DD formatında olmalı.
        - Sadece tek tarih varsa start_date ve end_date aynı gün olmalı.
        - Tarih yoksa start_date ve end_date null olmalı.
        - Türkçe ay adlarını doğru yorumla.

        Örnekler:
        Kullanıcı: "15 temmuz 15 ağustos arası herhangi bir etkinlik var mı"
        Cevap: {{"city": null, "category": null, "start_date": "2026-07-15", "end_date": "2026-08-15"}}

        Kullanıcı: "15 temmuz 15 ağustos arası istanbulda konser var mı"
        Cevap: {{"city": "İstanbul", "category": "Konser", "start_date": "2026-07-15", "end_date": "2026-08-15"}}

        Kullanıcı: "konya'da tiyatro var mı"
        Cevap: {{"city": "Konya", "category": "Tiyatro", "start_date": null, "end_date": null}}

        Sadece JSON dön. Açıklama yazma. Markdown kullanma.
        """

    response = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        stream=False,
        format=AI_FILTER_JSON_SCHEMA,
        options={
            "temperature": 0
        }
    )

    llm_output = response["message"]["content"].strip()
    return normalize_ai_intent(parse_llm_json(llm_output))

def extract_ai_chat_intent(messages, current_filters=None):
    today = date.today().isoformat()
    active_filters = filters_to_dict(current_filters)

    system_prompt = f"""
        Sen PortaBilet için çalışan konuşmalı etkinlik arama asistanısın.
        Bugünün tarihi: {today}.
        Mevcut aktif filtreler: {json.dumps(active_filters, ensure_ascii=False)}.

        Görevin veritabanını sorgulamak değildir. Veritabanına asla erişemezsin.
        Sadece konuşmadan niyeti çıkar ve JSON dön.

        JSON alanları:
        intent, filters, should_search, needs_clarification, assistant_reply.

        Kurallar:
        - intent sadece şu değerlerden biri olabilir: search_events, update_filters, reset_filters, smalltalk, help.
        - filters sadece city, category, start_date, end_date alanlarını içermeli.
        - Kullanıcı mevcut filtreleri temizlemek, sıfırlamak veya baştan başlamak isterse intent reset_filters olmalı, should_search false olmalı, needs_clarification false olmalı.
        - Kullanıcı "İstanbul ekle ama arama yapma", "şehri Ankara yap", "kategori konser olsun" gibi filtre günceller ama arama istemezse intent update_filters olmalı ve should_search false olmalı.
        - Kullanıcı açıkça arama isterse veya yeterli arama kriteri verirse intent search_events olmalı.
        - Tek bir filtre çoğu durumda yeterli değildir. Sadece kategori, sadece şehir veya sadece tarih varsa should_search false olmalı ve assistant_reply eksik kriteri veya "fark etmez mi?" seçeneğini sormalı.
        - Kullanıcı "fark etmez", "herhangi", "genel ara", "direkt ara" gibi geniş aramaya izin verirse tek filtreyle should_search true olabilir.
        - Kullanıcı arama için yeterince bilgi verdiyse veya geniş aramaya izin verdiyse should_search true olmalı.
        - Kullanıcı eğlenceli bir şeyler arıyorum gibi belirsiz arama yaparsa should_search false, needs_clarification true olmalı; assistant_reply doğal bir takip sorusu olmalı.
        - Kullanıcı selam, nasılsın, teşekkürler gibi sohbet ederse intent smalltalk olmalı, should_search false olmalı.
        - Kullanıcı nasıl kullanacağını sorarsa intent help olmalı, should_search false olmalı.
        - needs_clarification true ise assistant_reply doğal Türkçe bir takip sorusu olmalı; aynı kalıp cümleyi sürekli kullanma.
        - Kullanıcı bir filtre alanını açıkça belirtmediyse filters içinde o alan null olmalı; mevcut filtreleri değiştirme kararını backend birleştirecek.
        - Genel ifadeler kategori değildir. Örneğin "herhangi bir etkinlik", "etkinlik var mı", "ne var", "bir şey var mı" ifadelerinde category null olmalı.
        - category sadece şu değerlerden biri olabilir: Konser, Tiyatro, Festival, Stand-up, Spor.
        - Tarih varsa start_date ve end_date YYYY-MM-DD formatında olmalı.
        - Sadece tek tarih varsa start_date ve end_date aynı gün olmalı.
        - Tarih yoksa start_date ve end_date null olmalı.
        - Türkçe ay adlarını doğru yorumla.
        - Önceki assistant mesajlarını ve mevcut aktif filtreleri bağlam olarak kullan.

        Örnek:
        Kullanıcı: "Konser var mı?"
        Cevap: {{"intent": "search_events", "filters": {{"city": null, "category": "Konser", "start_date": null, "end_date": null}}, "should_search": false, "needs_clarification": true, "assistant_reply": "Konser için şehir veya tarih fark eder mi? Fark etmezse tüm konserlere bakabilirim."}}

        Örnek:
        Kullanıcı: "İstanbul ekle ama henüz arama"
        Cevap: {{"intent": "update_filters", "filters": {{"city": "İstanbul", "category": null, "start_date": null, "end_date": null}}, "should_search": false, "needs_clarification": false, "assistant_reply": "İstanbul'u filtrelere ekledim, arama yapmıyorum."}}

        Örnek:
        Kullanıcı: "konser olsun"
        Cevap: {{"intent": "update_filters", "filters": {{"city": null, "category": "Konser", "start_date": null, "end_date": null}}, "should_search": false, "needs_clarification": true, "assistant_reply": "Konser iyi. Şehir veya tarih fark eder mi, yoksa tüm konserlere mi bakayım?"}}

        Örnek:
        Kullanıcı: "fark etmez ara"
        Cevap: {{"intent": "search_events", "filters": {{"city": null, "category": null, "start_date": null, "end_date": null}}, "should_search": true, "needs_clarification": false, "assistant_reply": "Tamam, mevcut filtrelerle geniş arıyorum."}}

        Örnek:
        Kullanıcı: "Filtreleri temizle"
        Cevap: {{"intent": "reset_filters", "filters": {{"city": null, "category": null, "start_date": null, "end_date": null}}, "should_search": false, "needs_clarification": false, "assistant_reply": "Filtreleri temizledim."}}

        Örnek:
        Kullanıcı: "valla eğlenceli bir şeyler arıyorum"
        Cevap: {{"intent": "search_events", "filters": {{"city": null, "category": null, "start_date": null, "end_date": null}}, "should_search": false, "needs_clarification": true, "assistant_reply": "Nasıl bir eğlence olsun: konser, festival, tiyatro veya stand-up gibi bir tür seçelim mi?"}}

        Sadece JSON dön. Açıklama yazma. Markdown kullanma.
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

@router.post("/ai-search")
def ai_search_events(request: AISearchRequest, db: Session = Depends(get_db)):
    try:
        intent = extract_ai_search_intent(request.prompt)
        search_params = event_filters_from_intent(intent)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Yapay zeka analizi başarısız oldu: {str(e)}"
        )

    events = query_events_by_filters(db, search_params)

    return {
        "llm_extracted_data": search_params,
        "filters_applied": search_params,
        "events": events
    }

@router.post("/ai-chat")
def ai_chat_events(request: AIChatRequest, db: Session = Depends(get_db)):
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
                intent = enforce_slot_filling(intent, request.messages, current_slot_state)
            except Exception as e:
                logger.exception("AI chat analysis failed before response")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "message": "AI sohbet servisi şu anda yanıt vermiyor. Lütfen biraz sonra tekrar deneyin.",
                        "error_code": "AI_CHAT_UNAVAILABLE",
                        "technical_error": str(e),
                    },
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

@router.post("/")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    new_model = models.Event(
        title=event.title, 
        date=event.date, 
        location=event.location, 
        price=event.price, 
        description=event.description, 
        image=event.image,
        city=event.city,
        category=event.category,
        capacity=event.capacity,
        time=event.time
        )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return {"mesaj": "Etkinlik basariyla olusturuldu!"}

@router.get("/")
def get_all_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()

    for event in events:
        sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == event.id).count()
        event.available_tickets = event.capacity - sold_count

    return events

@router.get("/my-reviews")
def get_my_reviews(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    my_reviews = db.query(models.Review).options(joinedload(models.Review.event)).filter(models.Review.user_id == current_user.id).all()
    return my_reviews

@router.get("/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_tickets = db.query(models.Ticket).options(joinedload(models.Ticket.event)).filter(models.Ticket.user_id == current_user.id).all()

    for ticket in my_tickets:
        if ticket.event:
            sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == ticket.event.id).count()
            ticket.event.available_tickets = ticket.event.capacity - sold_count

    return my_tickets

@router.post("/ticket-transfer")
def ticket_transfer(payload: TicketTransferSchema, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == payload.id).first()
    
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Bilet bulunamadi!")
        
    if db_ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sadece kendi biletlerinizi transfer edebilirsiniz!")

    target_user = db.query(models.User).filter(models.User.email == payload.target_email).first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="Bu e-posta adresine sahip bir kullanici bulunamadi!")
        
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Bilet zaten size ait!")

    db_ticket.user_id = target_user.id
    db.commit()
    db.refresh(db_ticket)
    
    return {"mesaj": "Bilet basariyla transfer edildi!"}

@router.get("/my-favorites")
def get_my_favorites(current_user: models.User = Depends(get_current_user)):
    return current_user.favorite_events

@router.get("/{event_id:int}", response_model=EventSchema)
def get_single_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == event.id).count()
    event.available_tickets = event.capacity - sold_count

    return event

@router.post("/buy/{event_id:int}")
def buy_ticket(event_id: int, payment_data: PaymentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == event.id).count()

    if sold_count >= event.capacity:
        raise HTTPException(status_code=400, detail="Bu etkinlik icin stoklar tukendi!")
    
    options = {
        'api_key': os.getenv("IYZICO_API_KEY"),
        'secret_key': os.getenv("IYZICO_SECRET_KEY"),
        'base_url': os.getenv("IYZICO_BASE_URL")
    }

    request = {
        'locale': 'tr',
        'conversationId': '123456789',
        'price': str(event.price),
        'paidPrice': str(int(event.price) + 25),
        'currency': 'TRY',
        'installment': '1',
        'basketId': f'BASKET_{event_id}',
        'paymentChannel': 'WEB',
        'paymentGroup': 'PRODUCT',
        'paymentCard': {
            'cardHolderName': payment_data.cardHolderName,
            'cardNumber': payment_data.cardNumber,
            'expireMonth': payment_data.expireMonth,
            'expireYear': payment_data.expireYear,
            'cvc': payment_data.cvc,
            'registerCard': '0'
        },
        'buyer': {
            'id': 'BY789',
            'name': 'John',
            'surname': 'Doe',
            'gsmNumber': '+905350000000',
            'email': 'email@email.com',
            'identityNumber': '74300864791',
            'lastLoginDate': '2015-10-05 12:43:35',
            'registrationDate': '2013-04-21 15:12:09',
            'registrationAddress': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
            'ip': '85.34.78.112',
            'city': 'Istanbul',
            'country': 'Turkey',
            'zipCode': '34732'
        },
        'shippingAddress': {
            'contactName': 'Jane Doe',
            'city': 'Istanbul',
            'country': 'Turkey',
            'address': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
            'zipCode': '34742'
        },
        'billingAddress': {
            'contactName': 'Jane Doe',
            'city': 'Istanbul',
            'country': 'Turkey',
            'address': 'Nidakule Göztepe, Merdivenköy Mah. Bora Sok. No:1',
            'zipCode': '34742'
        },
        'basketItems': [
            {
                'id': str(event_id),
                'name': event.title,
                'category1': 'Bilet',
                'itemType': 'VIRTUAL',
                'price': str(event.price)
            }
        ]
    }

    payment_response = iyzipay.Payment().create(request, options)

    result = payment_response.read().decode('utf-8')

    if "success" not in result.lower():
        raise HTTPException(status_code=400, detail="Ödeme reddedildi! Lütfen kart bilgilerinizi kontrol edin.")
    
    message_body = {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "event_id": event.id,
        "event_title": event.title
    }

    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message_body)
    )

    return {"mesaj": f"Ödeme başarıyla alındı, {current_user.email} adlı kullanıcı {event.title} etkinliğine başarıyla bilet aldı!"}

@router.delete("/{event_id:int}")
def delete_event(event_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bu islem icin yetkiniz yok!")
    
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")
    
    db.query(models.Ticket).filter(models.Ticket.event_id == event_id).delete(synchronize_session=False)
        
    db.delete(event)
    db.commit()

    return {"mesaj": "Etkinlik basariyla silindi!"}

@router.post("/toggle-favorite/{event_id:int}")
def toggle_favorite(event_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not db_event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    if db_event not in current_user.favorite_events:
        current_user.favorite_events.append(db_event)
        is_added = True
    
    else:
        current_user.favorite_events.remove(db_event)
        is_added = False

    db.commit()

    if is_added:
        return {"mesaj": "Etkinlik favorilere eklendi!", "status": "added"}
    else:
        return {"mesaj": "Etkinlik favorilerden cikarildi!", "status": "removed"}

@router.post("/{event_id:int}/reviews")
def create_review(event_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not db_event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")
    
    has_ticket = db.query(models.Ticket).filter(
        models.Ticket.user_id == current_user.id,
        models.Ticket.event_id == event_id
    ).first()

    if not has_ticket:
        raise HTTPException(status_code=403, detail="Sadece bilet aldiginiz etkinliklere degerlendirme yapabilirsiniz!")
    
    existing_review = db.query(models.Review).filter(
        models.Review.user_id == current_user.id,
        models.Review.event_id == event_id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="Bu etkinliği zaten değerlendirdiniz!")
    
    new_review = models.Review(
        rating=review.rating,
        comment=review.comment,
        user_id=current_user.id,
        event_id=event_id
    )

    db.add(new_review)
    db.commit()

    return {"mesaj": "Degerlendirmeniz basariyla eklendi!"}

@router.get("/{event_id:int}/reviews")
def get_all_reviews(event_id: int, db: Session = Depends(get_db)):
    current_event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not current_event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadi!")

    similar_events = db.query(models.Event).filter(models.Event.title == current_event.title).all()
    similar_events_ids = [e.id for e in similar_events]

    all_reviews = db.query(models.Review).options(
        joinedload(models.Review.user),
        joinedload(models.Review.event)
    ).filter(models.Review.event_id.in_(similar_events_ids)).all()

    return all_reviews

@router.get("/{id:int}/calendar")
def calendar(id: int, db: Session = Depends(get_db)):
    db_event = db.query(models.Event).filter(models.Event.id == id).first()

    if not db_event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")
    
    formatted_date = str(db_event.date).replace("-", "")
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PortaBilet//TR
BEGIN:VEVENT
SUMMARY:{db_event.title}
DESCRIPTION:PortaBilet üzerinden aldığınız etkinlik.
DTSTART;VALUE=DATE:{formatted_date}
LOCATION:{db_event.location}
END:VEVENT
END:VCALENDAR"""

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=portabilet_etkinlik_{id}.ics"}
        )

@router.get("/{event_id:int}/weather")
def get_event_weather(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadi!")
    
    event_date = datetime.strptime(event.date, "%Y-%m-%d").date()
    today = datetime.now().date()

    days_diff = (event_date - today).days

    if days_diff < 0:
        return {"status": "unavailable", "message": "Etkinligin gunu gecmis."}
    elif days_diff > 5:
        return {"status": "unavailable", "message": "Tahmin için erken."}
    else:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        city = event.city

        try:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},TR&limit=1&appid={api_key}"
            geo_response = requests.get(geo_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]

            weather_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=tr"
            weather_response = requests.get(weather_url)
            weather_response.raise_for_status()
            data = weather_response.json()

            return {"status": "success", "data": data}
            
        except Exception as e:
            return {"status": "error", "message": f"Hava durumu cekilemedi: {str(e)}"}
        
@router.get("/{event_id:int}/recommendations", response_model=list[EventSchema])
def get_recommendations(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadi!")
    
    recommendations = db.query(models.Event).filter(
        models.Event.category == event.category,
        models.Event.id != event_id
    ).limit(3).all()

    for rec in recommendations:
        sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == rec.id).count()
        rec.available_tickets = rec.capacity - sold_count

    return recommendations

# @router.get("/fix-database-columns")
# def fix_db(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("ALTER TABLE events ADD COLUMN image VARCHAR;"))
#         db.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS description VARCHAR;"))
#         db.commit()
#         return {"mesaj": "Veritabanina image ve desc kolonlari basariyla eklendi!"}
#     except Exception as e:
#         return {"hata": f"detay: {str(e)}"}

# @router.get("/fix-database-v2")
# def fix_db_v2(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS city VARCHAR DEFAULT 'İstanbul';"))
#         db.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS category VARCHAR DEFAULT 'Konser';"))
#         db.commit()
#         return {"mesaj": "Sehir ve Kategori kolonlari basariyla eklendi!"}
#     except Exception as e:
#         return {"hata": "Zaten eklenmis veya bir sorun var", "detay": str(e)}
