from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from fastapi import HTTPException
import jwt
from passlib.context import CryptContext

import models


load_dotenv()

SECRET_KEY = os.getenv("OAUTH2_SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def register_user(db, user):
    hashedPassword = pwd_context.hash(user.password[:72])
    newUser = models.User(name=user.name, email=user.email, password=hashedPassword)
    db.add(newUser)
    db.commit()
    return {"mesaj": f"{user.email} adresiyle kayit islemi basariyla yapildi."}


def login_user(db, form_data):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi!")

    if not pwd_context.verify(form_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Sifre hatali!")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": db_user.is_admin}


def get_user_from_token(db, token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Kimlik doğrulanamadı")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi dolmuş, tekrar giriş yapın")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")

    return user


def get_my_profile(current_user):
    return {
        "name": current_user.name,
        "email": current_user.email
    }


def update_profile(db, current_user, profile):
    current_user.name = profile.name
    db.commit()
    db.refresh(current_user)

    return {"mesaj": "Profil basariyla degistirildi!"}


def update_password(db, current_user, passwords):
    is_password_correct = pwd_context.verify(passwords.current_password[:72], current_user.password)

    if not is_password_correct:
        raise HTTPException(status_code=400, detail="Mevcut sifreniz yanlis!")

    current_user.password = pwd_context.hash(passwords.new_password[:72])

    db.commit()

    return {"mesaj": "Sifreniz basariyla degistirildi!"}


def delete_account(db, current_user, request):
    if current_user.email != request.email:
        raise HTTPException(status_code=400, detail="Girdiğiniz e-posta adresi hesabınızla uyuşmuyor!")

    db.query(models.Ticket).filter(models.Ticket.user_id == current_user.id).delete(synchronize_session=False)

    db.query(models.Review).filter(models.Review.user_id == current_user.id).delete(synchronize_session=False)

    current_user.favorite_events.clear()

    db.delete(current_user)
    db.commit()

    return {"mesaj": "Hesap başarıyla silindi."}


def update_email_notifications(db, current_user, request):
    current_user.email_notifications = request.email_notifications

    db.commit()

    return {"mesaj": "Email bildirim ayarı başarıyla güncellendi."}


def make_admin(db, email):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return {"hata": "Böyle bir kullanıcı bulunamadı!"}

    user.is_admin = True
    db.commit()
    return {"mesaj": f"Tebrikler, {email} hesabı başarıyla Admin yapıldı!"}
