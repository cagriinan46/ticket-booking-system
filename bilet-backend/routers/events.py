from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import get_current_user
from fastapi import HTTPException
from dotenv import load_dotenv
import models
import iyzipay
import boto3
import json
import os

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

class EventSchema(BaseModel):
    id: int
    title: str
    date: str
    location: str
    price: str

    class Config:
        from_attributes = True

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


@router.post("/")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    new_model = models.Event(title=event.title, date=event.date, location=event.location, price=event.price)
    db.add(new_model)
    db.commit()
    return {"mesaj": "Etkinlik basariyla olusturuldu!"}

@router.get("/")
def get_all_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return events

@router.post("/buy/{event_id}")
def buy_ticket(event_id: int, payment_data: PaymentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")
    
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

@router.get("/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_tickets = db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).all()
    return my_tickets

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

    


    
