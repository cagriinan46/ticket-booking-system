from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from routers.auth import get_current_user
from schemas.ai import AIChatRequest, AISearchRequest
from schemas.events import EventCreate, EventSchema
from schemas.payments import PaymentRequest
from schemas.reviews import ReviewCreate
from schemas.tickets import TicketResponse, TicketTransferSchema
from services import (
    ai_chat_service,
    ai_search_service,
    calendar_service,
    event_service,
    favorite_service,
    payment_service,
    recommendation_service,
    review_service,
    ticket_service,
    weather_service,
)


router = APIRouter(
    prefix="/api/events",
    tags=["Events"]
)


@router.post("/ai-search")
def ai_search_events(request: AISearchRequest, db: Session = Depends(get_db)):
    try:
        intent = ai_search_service.extract_ai_search_intent(request.prompt)
        search_params = ai_search_service.event_filters_from_intent(intent)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Yapay zeka analizi başarısız oldu: {str(e)}"
        )

    events = event_service.query_events_by_filters(db, search_params)

    return {
        "llm_extracted_data": search_params,
        "filters_applied": search_params,
        "events": events
    }


@router.post("/ai-chat")
def ai_chat_events(request: AIChatRequest, db: Session = Depends(get_db)):
    return ai_chat_service.handle_ai_chat_events(request, db)


@router.post("/")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    return event_service.create_event(db, event)


@router.get("/")
def get_all_events(db: Session = Depends(get_db)):
    return event_service.get_all_events(db)


@router.get("/my-reviews")
def get_my_reviews(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return review_service.get_my_reviews(db, current_user)


@router.get("/my-tickets", response_model=list[TicketResponse])
def get_my_tickets(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ticket_service.get_my_tickets(db, current_user)


@router.post("/ticket-transfer")
def ticket_transfer(payload: TicketTransferSchema, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return ticket_service.transfer_ticket(db, current_user, payload)


@router.get("/my-favorites")
def get_my_favorites(current_user: models.User = Depends(get_current_user)):
    return favorite_service.get_my_favorites(current_user)


@router.get("/{event_id:int}", response_model=EventSchema)
def get_single_event(event_id: int, db: Session = Depends(get_db)):
    return event_service.get_single_event(db, event_id)


@router.post("/buy/{event_id:int}")
def buy_ticket(event_id: int, payment_data: PaymentRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return payment_service.buy_ticket(db, current_user, event_id, payment_data)


@router.delete("/{event_id:int}")
def delete_event(event_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return event_service.delete_event(db, event_id, current_user)


@router.post("/toggle-favorite/{event_id:int}")
def toggle_favorite(event_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return favorite_service.toggle_favorite(db, current_user, event_id)


@router.post("/{event_id:int}/reviews")
def create_review(event_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return review_service.create_review(db, current_user, event_id, review)


@router.get("/{event_id:int}/reviews")
def get_all_reviews(event_id: int, db: Session = Depends(get_db)):
    return review_service.get_all_reviews(db, event_id)


@router.get("/{id:int}/calendar")
def calendar(id: int, db: Session = Depends(get_db)):
    return calendar_service.build_calendar_response(db, id)


@router.get("/{event_id:int}/weather")
def get_event_weather(event_id: int, db: Session = Depends(get_db)):
    return weather_service.get_event_weather(db, event_id)


@router.get("/{event_id:int}/recommendations", response_model=list[EventSchema])
def get_recommendations(event_id: int, db: Session = Depends(get_db)):
    return recommendation_service.get_recommendations(db, event_id)
