from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from fastapi import HTTPException
from dotenv import load_dotenv
from typing import Literal, Optional
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import joinedload
from datetime import date
from ollama import Client
import models
import iyzipay
import boto3
import json
import os
import requests
import ollama

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

class AIChatRequest(BaseModel):
    messages: list[AIChatMessage]

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

ollama_client = Client(
    host=OLLAMA_HOST,
    timeout=60.0
)

FILTER_KEYS = ["city", "category", "start_date", "end_date"]
INVALID_AI_VALUES = ["null", "", "yok", "belirtilmemiş", "belirtilmemis", "none"]

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
        },
        "needs_clarification": {
            "type": "boolean"
        },
        "follow_up_question": {
            "type": ["string", "null"]
        }
    },
    "required": [
        "city",
        "category",
        "start_date",
        "end_date",
        "needs_clarification",
        "follow_up_question"
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

def event_filters_from_intent(intent):
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
    if intent.get("needs_clarification"):
        return intent.get("follow_up_question")

    filter_text = describe_filters(intent)

    if events:
        if filter_text:
            return f"{filter_text} kriterleriyle {len(events)} etkinlik buldum."
        return f"Aramana uygun {len(events)} etkinlik buldum."

    if filter_text:
        return f"{filter_text} kriterlerine uygun etkinlik bulamadım. Farklı bir şehir, tarih veya kategori deneyebilirsiniz."

    return "Aramana uygun etkinlik bulamadım. Şehir, tarih veya kategori ekleyerek tekrar deneyebilirsiniz."

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

def extract_ai_chat_intent(messages):
    today = date.today().isoformat()

    system_prompt = f"""
        Sen PortaBilet için çalışan konuşmalı etkinlik arama asistanısın.
        Bugünün tarihi: {today}.

        Görevin veritabanını sorgulamak değildir. Veritabanına asla erişemezsin.
        Sadece konuşmadan arama niyetini çıkar ve JSON dön.

        JSON alanları:
        city, category, start_date, end_date, needs_clarification, follow_up_question.

        Kurallar:
        - Kullanıcı en az bir somut arama kriteri verdiyse needs_clarification false olmalı.
        - Hiç şehir, kategori veya tarih yoksa needs_clarification true olmalı.
        - needs_clarification true ise follow_up_question doğal Türkçe bir soru olmalı.
        - needs_clarification false ise follow_up_question null olmalı.
        - Kullanıcı bir alanı açıkça belirtmediyse o alan null olmalı.
        - Genel ifadeler kategori değildir. Örneğin "herhangi bir etkinlik", "etkinlik var mı", "ne var", "bir şey var mı" ifadelerinde category null olmalı.
        - category sadece şu değerlerden biri olabilir: Konser, Tiyatro, Festival, Stand-up, Spor.
        - Tarih varsa start_date ve end_date YYYY-MM-DD formatında olmalı.
        - Sadece tek tarih varsa start_date ve end_date aynı gün olmalı.
        - Tarih yoksa start_date ve end_date null olmalı.
        - Türkçe ay adlarını doğru yorumla.
        - Önceki assistant mesajlarını sadece bağlam olarak kullan.

        Örnek:
        Kullanıcı: "Konser var mı?"
        Cevap: {{"city": null, "category": "Konser", "start_date": null, "end_date": null, "needs_clarification": false, "follow_up_question": null}}

        Örnek:
        Kullanıcı: "Bir şeyler bakıyorum"
        Cevap: {{"city": null, "category": null, "start_date": null, "end_date": null, "needs_clarification": true, "follow_up_question": "Hangi şehirde veya hangi türde etkinlik arıyorsunuz?"}}

        Sadece JSON dön. Açıklama yazma. Markdown kullanma.
        """

    ollama_messages = [{"role": "system", "content": system_prompt}]
    ollama_messages.extend(
        {"role": message.role, "content": message.content.strip()}
        for message in messages
        if message.content.strip()
    )

    response = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=ollama_messages,
        stream=False,
        format=AI_CHAT_JSON_SCHEMA,
        options={
            "temperature": 0
        }
    )

    llm_output = response["message"]["content"].strip()
    return normalize_ai_intent(parse_llm_json(llm_output))

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

    try:
        intent = extract_ai_chat_intent(request.messages)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Yapay zeka sohbet analizi başarısız oldu: {str(e)}"
        )

    filters = event_filters_from_intent(intent)

    if intent.get("needs_clarification"):
        return {
            "reply": build_ai_chat_reply([], intent),
            "filters_applied": filters,
            "events": [],
            "needs_clarification": True
        }

    events = query_events_by_filters(db, filters)

    return {
        "reply": build_ai_chat_reply(events, intent),
        "filters_applied": filters,
        "events": events,
        "needs_clarification": False
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

@router.get("/{event_id}", response_model=EventSchema)
def get_single_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == event.id).count()
    event.available_tickets = event.capacity - sold_count

    return event

@router.post("/buy/{event_id}")
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

@router.delete("/{event_id}")
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

@router.post("/toggle-favorite/{event_id}")
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

@router.post("/{event_id}/reviews")
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

@router.get("/{event_id}/reviews")
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

@router.get("/{id}/calendar")
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

@router.get("/{event_id}/weather")
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
        
@router.get("/{event_id}/recommendations", response_model=list[EventSchema])
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
