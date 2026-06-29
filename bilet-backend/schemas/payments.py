from pydantic import BaseModel


class PaymentRequest(BaseModel):
    cardHolderName: str
    cardNumber: str
    expireMonth: str
    expireYear: str
    cvc: str
