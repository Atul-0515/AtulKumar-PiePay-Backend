from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Request schema for POST /offer
class OfferRequest(BaseModel):
    flipkartOfferApiResponse: Dict[str, Any]


# Response schema for POST /offer
class OfferResponse(BaseModel):
    noOfOffersIdentified: int
    noOfNewOffersCreated: int


# Response schema for GET /highest-discount
class HighestDiscountResponse(BaseModel):
    highestDiscountAmount: float


# Internal schemas for database operations
class BankBase(BaseModel):
    bank_code: str
    bank_name: Optional[str] = None


class BankCreate(BankBase):
    pass


class Bank(BankBase):
    id: int

    class Config:
        from_attributes = True


class PaymentInstrumentBase(BaseModel):
    instrument_type: str


class PaymentInstrumentCreate(PaymentInstrumentBase):
    pass


class PaymentInstrument(PaymentInstrumentBase):
    id: int

    class Config:
        from_attributes = True


class OfferBase(BaseModel):
    offer_id: str
    offer_text: str
    offer_description: str
    logo: Optional[str] = None


class OfferCreate(OfferBase):
    bank_codes: List[str] = []
    payment_instruments: List[str] = []


class Offer(OfferBase):
    id: int
    banks: List[Bank] = []
    payment_instruments: List[PaymentInstrument] = []

    class Config:
        from_attributes = True