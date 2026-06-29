from datetime import datetime
import os

from dotenv import load_dotenv
from fastapi import HTTPException
import requests

import models


load_dotenv()

def get_event_weather(db, event_id):
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
