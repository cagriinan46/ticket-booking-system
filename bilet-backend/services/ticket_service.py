from fastapi import HTTPException
from sqlalchemy.orm import joinedload

import models


def get_my_tickets(db, current_user):
    my_tickets = db.query(models.Ticket).options(joinedload(models.Ticket.event)).filter(models.Ticket.user_id == current_user.id).all()

    for ticket in my_tickets:
        if ticket.event:
            sold_count = db.query(models.Ticket).filter(models.Ticket.event_id == ticket.event.id).count()
            ticket.event.available_tickets = ticket.event.capacity - sold_count

    return my_tickets


def transfer_ticket(db, current_user, payload):
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
