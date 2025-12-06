from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Association table for many-to-many relationship between Offer and Bank
offer_bank_association = Table(
    'offer_bank_association',
    Base.metadata,
    Column('offer_id', Integer, ForeignKey('offers.id'), primary_key=True),
    Column('bank_id', Integer, ForeignKey('banks.id'), primary_key=True)
)

# Association table for many-to-many relationship between Offer and PaymentInstrument
offer_payment_instrument_association = Table(
    'offer_payment_instrument_association',
    Base.metadata,
    Column('offer_id', Integer, ForeignKey('offers.id'), primary_key=True),
    Column('payment_instrument_id', Integer, ForeignKey('payment_instruments.id'), primary_key=True)
)


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(String, unique=True, index=True, nullable=False)  # Flipkart's offer ID
    offer_text = Column(String, nullable=False)  # e.g., "Get ₹10 cashback"
    offer_description = Column(String, nullable=False)  # Full terms and conditions
    logo = Column(String, nullable=True)  # Logo URL
    
    # Relationships
    banks = relationship("Bank", secondary=offer_bank_association, back_populates="offers")
    payment_instruments = relationship("PaymentInstrument", secondary=offer_payment_instrument_association, back_populates="offers")

    def __repr__(self):
        return f"<Offer(offer_id='{self.offer_id}', offer_text='{self.offer_text}')>"


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    bank_code = Column(String, unique=True, index=True, nullable=False)  # e.g., "AXIS", "HDFC"
    bank_name = Column(String, nullable=True)  # Full bank name (optional)
    
    # Relationships
    offers = relationship("Offer", secondary=offer_bank_association, back_populates="banks")

    def __repr__(self):
        return f"<Bank(bank_code='{self.bank_code}')>"


class PaymentInstrument(Base):
    __tablename__ = "payment_instruments"

    id = Column(Integer, primary_key=True, index=True)
    instrument_type = Column(String, unique=True, index=True, nullable=False)  # e.g., "CREDIT", "EMI_OPTIONS"
    
    # Relationships
    offers = relationship("Offer", secondary=offer_payment_instrument_association, back_populates="payment_instruments")

    def __repr__(self):
        return f"<PaymentInstrument(instrument_type='{self.instrument_type}')>"