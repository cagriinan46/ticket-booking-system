from fastapi import HTTPException
from sqlalchemy.orm import joinedload

import models


def get_my_reviews(db, current_user):
    return db.query(models.Review).options(joinedload(models.Review.event)).filter(models.Review.user_id == current_user.id).all()


def create_review(db, current_user, event_id, review):
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


def get_all_reviews(db, event_id):
    current_event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not current_event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadi!")

    similar_events = db.query(models.Event).filter(models.Event.title == current_event.title).all()
    similar_events_ids = [e.id for e in similar_events]

    return db.query(models.Review).options(
        joinedload(models.Review.user),
        joinedload(models.Review.event)
    ).filter(models.Review.event_id.in_(similar_events_ids)).all()
