from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from database import get_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
import jwt
import models
import os

load_dotenv()

SECRET_KEY = os.getenv("OAUTH2_SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

pwd_context = CryptContext(schemes= ["bcrypt"], deprecated= "auto")

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class ProfileUpdate(BaseModel):
    name: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    hashedPassword = pwd_context.hash(user.password[:72])
    newUser = models.User(name= user.name, email= user.email, password= hashedPassword)
    db.add(newUser)
    db.commit()
    return {"mesaj": f"{user.email} adresiyle kayit islemi basariyla yapildi."}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi!")

    if not pwd_context.verify(form_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Sifre hatali!")
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "is_admin": db_user.is_admin}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

@router.get("/users/me")
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email
    }

@router.get("/make-admin/{email}")
def make_admin(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return {"hata": "Böyle bir kullanıcı bulunamadı!"}

    user.is_admin = True
    db.commit()
    return {"mesaj": f"Tebrikler, {email} hesabı başarıyla Admin yapıldı!"}

@router.put("/users/me/profile")
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.name = profile.name
    db.commit()
    db.refresh(current_user)

    return {"mesaj": "Profil basariyla degistirildi!"}

@router.put("/users/me/password")
def update_password(passwords: PasswordUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    is_password_correct = pwd_context.verify(passwords.current_password[:72], current_user.password)

    if not is_password_correct:
        raise HTTPException(status_code=400, detail="Mevcut sifreniz yanlis!")
    
    current_user.password = pwd_context.hash(passwords.new_password[:72])
    
    db.commit()

    return {"mesaj": "Sifreniz basariyla degistirildi!"}