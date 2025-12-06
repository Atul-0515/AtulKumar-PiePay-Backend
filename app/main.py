from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, engine, Base
from app import schemas, crud
from app.utils import parse_offers_from_flipkart_response, calculate_discount

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="PiePay Backend API",
    description="API to detect and store Flipkart offers and calculate best discounts",
    version="1.0.0"
)


@app.get("/")
def read_root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "Welcome to PiePay Backend API",
        "status": "running",
        "endpoints": {
            "POST /offer": "Store offers from Flipkart response",
            "GET /highest-discount": "Calculate highest discount for payment details"
        }
    }


@app.post("/offer", response_model=schemas.OfferResponse)
def create_offers(
    request: schemas.OfferRequest,
    db: Session = Depends(get_db)
):
    """
    Parse and store offers from Flipkart's offer API response.
    
    **Request Body:**
    ```json
    {
        "flipkartOfferApiResponse": {
            // Flipkart's complete response object
        }
    }
    ```
    
    **Response:**
    ```json
    {
        "noOfOffersIdentified": 5,
        "noOfNewOffersCreated": 3
    }
    ```
    """
    try:
        # Parse offers from Flipkart response
        parsed_offers = parse_offers_from_flipkart_response(
            request.flipkartOfferApiResponse
        )
        
        if not parsed_offers:
            return schemas.OfferResponse(
                noOfOffersIdentified=0,
                noOfNewOffersCreated=0
            )
        
        # Create offers in batch
        total_identified, new_created = crud.create_offers_batch(db, parsed_offers)
        
        return schemas.OfferResponse(
            noOfOffersIdentified=total_identified,
            noOfNewOffersCreated=new_created
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing offers: {str(e)}"
        )


@app.get("/highest-discount", response_model=schemas.HighestDiscountResponse)
def get_highest_discount(
    amountToPay: float = Query(..., description="Total amount to pay in rupees"),
    bankName: str = Query(..., description="Bank code (e.g., AXIS, HDFC, ICICI)"),
    paymentInstrument: Optional[str] = Query(None, description="Payment instrument type (e.g., CREDIT, EMI_OPTIONS)"),
    db: Session = Depends(get_db)
):
    """
    Calculate the highest discount amount for given payment details.
    
    **Query Parameters:**
    - `amountToPay`: Total amount to pay (in rupees)
    - `bankName`: Bank code as per Flipkart standards (AXIS, HDFC, etc.)
    - `paymentInstrument` (optional): Payment instrument (CREDIT, EMI_OPTIONS, etc.)
    
    **Example:**
    ```
    GET /highest-discount?amountToPay=10000&bankName=AXIS
    GET /highest-discount?amountToPay=10000&bankName=AXIS&paymentInstrument=CREDIT
    ```
    
    **Response:**
    ```json
    {
        "highestDiscountAmount": 500.0
    }
    ```
    """
    try:
        # Get applicable offers based on payment instrument
        if paymentInstrument:
            offers = crud.get_offers_by_bank_and_instrument(db, bankName, paymentInstrument)
        else:
            offers = crud.get_offers_by_bank(db, bankName)
        
        if not offers:
            return schemas.HighestDiscountResponse(highestDiscountAmount=0.0)
        
        # Calculate discount for each offer and find the highest
        max_discount = 0.0
        
        for offer in offers:
            discount = calculate_discount(
                offer.offer_text,
                offer.offer_description,
                amountToPay
            )
            
            if discount > max_discount:
                max_discount = discount
        
        return schemas.HighestDiscountResponse(highestDiscountAmount=max_discount)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating discount: {str(e)}"
        )


@app.get("/offers")
def get_all_offers(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all stored offers (for debugging/testing).
    """
    offers = crud.get_all_offers(db, skip=skip, limit=limit)
    return {
        "total": len(offers),
        "offers": [
            {
                "offer_id": offer.offer_id,
                "offer_text": offer.offer_text,
                "banks": [bank.bank_code for bank in offer.banks],
                "payment_instruments": [pi.instrument_type for pi in offer.payment_instruments]
            }
            for offer in offers
        ]
    }


@app.delete("/offers")
def delete_all_offers(db: Session = Depends(get_db)):
    """
    Delete all offers (for testing/reset).
    """
    count = crud.delete_all_offers(db)
    return {
        "message": f"Successfully deleted {count} offers"
    }
