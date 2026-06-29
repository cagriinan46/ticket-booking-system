from fastapi import HTTPException

import models


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


def create_event(db, event):
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


def get_all_events(db):
    events = db.query(models.Event).all()
    attach_available_tickets(db, events)
    return events


def get_single_event(db, event_id):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    attach_available_tickets(db, [event])
    return event


def delete_event(db, event_id, current_user):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Bu islem icin yetkiniz yok!")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Boyle bir etkinlik bulunamadi!")

    db.query(models.Ticket).filter(models.Ticket.event_id == event_id).delete(synchronize_session=False)

    db.delete(event)
    db.commit()

    return {"mesaj": "Etkinlik basariyla silindi!"}
