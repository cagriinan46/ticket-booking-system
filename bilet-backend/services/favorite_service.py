from fastapi import HTTPException

import models


def get_my_favorites(current_user):
    return current_user.favorite_events


def toggle_favorite(db, current_user, event_id):
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
