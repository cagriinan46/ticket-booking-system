from pydantic import BaseModel


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class ProfileUpdate(BaseModel):
    name: str


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    email: str


class EmailNotifRequest(BaseModel):
    email_notifications: bool
