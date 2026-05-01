from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from fastapi import HTTPException
from dotenv import load_dotenv
from typing import Optional
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.orm import joinedload
import models
import iyzipay
import boto3
import json
import os
import requests


load_dotenv()

sqs = boto3.client('sqs', region_name='eu-central-1')
SQS_QUEUE_URL = os.getenv("SQS_URL")

router = APIRouter(
    prefix="/api/events",
    tags=["Events"]
)

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
    my_reviews = db.query(models.Review).filter(models.Review.user_id == current_user.id).all()
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
    all_reviews = db.query(models.Review).filter(models.Review.event_id == event_id).all()
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