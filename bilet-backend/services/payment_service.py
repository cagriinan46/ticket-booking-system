import json
import os

import boto3
from dotenv import load_dotenv
from fastapi import HTTPException
import iyzipay

import models


load_dotenv()

sqs = boto3.client('sqs', region_name='eu-central-1')
SQS_QUEUE_URL = os.getenv("SQS_URL")


def buy_ticket(db, current_user, event_id, payment_data):
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
