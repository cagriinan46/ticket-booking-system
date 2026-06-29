from fastapi import HTTPException, Response

import models


def build_calendar_response(db, event_id):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()

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
        headers={"Content-Disposition": f"attachment; filename=portabilet_etkinlik_{event_id}.ics"}
    )
