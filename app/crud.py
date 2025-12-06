from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app import models, schemas


def get_or_create_bank(db: Session, bank_code: str, commit: bool = False) -> models.Bank:
    """
    Get existing bank or create new one.
    """
    bank = db.query(models.Bank).filter(models.Bank.bank_code == bank_code).first()
    if not bank:
        bank = models.Bank(bank_code=bank_code)
        db.add(bank)
        if commit:
            db.commit()
            db.refresh(bank)
    return bank


def get_or_create_payment_instrument(db: Session, instrument_type: str, commit: bool = False) -> models.PaymentInstrument:
    """
    Get existing payment instrument or create new one.
    """
    instrument = db.query(models.PaymentInstrument).filter(
        models.PaymentInstrument.instrument_type == instrument_type
    ).first()
    
    if not instrument:
        instrument = models.PaymentInstrument(instrument_type=instrument_type)
        db.add(instrument)
        if commit:
            db.commit()
            db.refresh(instrument)
    
    return instrument


def get_offer_by_offer_id(db: Session, offer_id: str) -> Optional[models.Offer]:
    """
    Get offer by Flipkart's offer_id.
    """
    return db.query(models.Offer).filter(models.Offer.offer_id == offer_id).first()


def create_offer(db: Session, offer_data: dict) -> models.Offer:
    """
    Create a new offer with associated banks and payment instruments.
    
    Args:
        offer_data: Dict with keys:
            - offer_id: str
            - offer_text: str
            - offer_description: str
            - logo: str
            - bank_codes: List[str]
            - payment_instruments: List[str]
    
    Returns:
        Created Offer model instance
    """
    # Create the offer
    offer = models.Offer(
        offer_id=offer_data['offer_id'],
        offer_text=offer_data['offer_text'],
        offer_description=offer_data['offer_description'],
        logo=offer_data.get('logo', '')
    )
    
    db.add(offer)
    db.flush()  # Flush to get offer ID
    
    # Add banks (get or create without committing)
    for bank_code in offer_data.get('bank_codes', []):
        bank = get_or_create_bank(db, bank_code, commit=False)
        if bank not in offer.banks:
            offer.banks.append(bank)
    
    # Add payment instruments (get or create without committing)
    for instrument_type in offer_data.get('payment_instruments', []):
        instrument = get_or_create_payment_instrument(db, instrument_type, commit=False)
        if instrument not in offer.payment_instruments:
            offer.payment_instruments.append(instrument)
    
    return offer


def create_offers_batch(db: Session, offers_data: List[dict]) -> Tuple[int, int]:
    """
    Create multiple offers in batch.
    
    Returns:
        Tuple of (total_offers_identified, new_offers_created)
    """
    total_identified = len(offers_data)
    new_created = 0
    
    for offer_data in offers_data:
        # Check if offer already exists
        existing_offer = get_offer_by_offer_id(db, offer_data['offer_id'])
        
        if not existing_offer:
            create_offer(db, offer_data)
            new_created += 1
    
    db.commit()
    
    return total_identified, new_created


def get_offers_by_bank(db: Session, bank_name: str) -> List[models.Offer]:
    """
    Get all offers that support a specific bank.
    
    Args:
        bank_name: Bank code (e.g., "AXIS", "HDFC")
    
    Returns:
        List of Offer models
    """
    return db.query(models.Offer).join(
        models.Offer.banks
    ).filter(
        models.Bank.bank_code == bank_name
    ).all()


def get_offers_by_bank_and_instrument(
    db: Session, 
    bank_name: str, 
    payment_instrument: str
) -> List[models.Offer]:
    """
    Get all offers that support a specific bank and payment instrument.
    
    Args:
        bank_name: Bank code (e.g., "AXIS", "HDFC")
        payment_instrument: Payment instrument type (e.g., "CREDIT", "EMI_OPTIONS")
    
    Returns:
        List of Offer models
    """
    return db.query(models.Offer).join(
        models.Offer.banks
    ).join(
        models.Offer.payment_instruments
    ).filter(
        models.Bank.bank_code == bank_name,
        models.PaymentInstrument.instrument_type == payment_instrument
    ).all()


def get_all_offers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Offer]:
    """
    Get all offers with pagination.
    """
    return db.query(models.Offer).offset(skip).limit(limit).all()


def delete_all_offers(db: Session) -> int:
    """
    Delete all offers (useful for testing/reset).
    Returns number of deleted offers.
    """
    count = db.query(models.Offer).count()
    db.query(models.Offer).delete()
    db.commit()
    return count