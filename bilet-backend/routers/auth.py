from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas.auth import (
    DeleteAccountRequest,
    EmailNotifRequest,
    PasswordUpdate,
    ProfileUpdate,
    UserRegister,
)
from services import auth_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    return auth_service.register_user(db, user)


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth_service.login_user(db, form_data)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auth_service.get_user_from_token(db, token)


@router.get("/me")
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return auth_service.get_my_profile(current_user)


@router.put("/me/profile")
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return auth_service.update_profile(db, current_user, profile)


@router.put("/me/password")
def update_password(passwords: PasswordUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return auth_service.update_password(db, current_user, passwords)


@router.delete("/delete-account")
def delete_account(request: DeleteAccountRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_service.delete_account(db, current_user, request)


@router.put("/email-notifications")
def update_email_notif(request: EmailNotifRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return auth_service.update_email_notifications(db, current_user, request)


@router.get("/make-admin/{email}")
def make_admin(email: str, db: Session = Depends(get_db)):
    return auth_service.make_admin(db, email)
