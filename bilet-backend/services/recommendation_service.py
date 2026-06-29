from fastapi import HTTPException

import models
from services.event_service import attach_available_tickets


def get_recommendations(db, event_id):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadi!")

    recommendations = db.query(models.Event).filter(
        models.Event.category == event.category,
        models.Event.id != event_id
    ).limit(3).all()

    attach_available_tickets(db, recommendations)

    return recommendations
