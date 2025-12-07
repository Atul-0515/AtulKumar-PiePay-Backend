"""
Test suite for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean database before each test"""
    yield
    # Clean up after test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "endpoints" in data


def test_post_offer_success():
    """Test creating offers successfully"""
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["AXIS"],
                                            "offerText": {"text": "Get ₹100 cashback"},
                                            "offerDescription": {
                                                "id": "TEST001",
                                                "text": "Test offer"
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "type": "PAYMENT_OPTION",
                            "data": {"instrumentType": "CREDIT"}
                        }
                    ]
                }
            }
        }
    }
    
    response = client.post("/offer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["noOfOffersIdentified"] == 1
    assert data["noOfNewOffersCreated"] == 1


def test_post_offer_duplicate():
    """Test duplicate offer prevention"""
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["AXIS"],
                                            "offerText": {"text": "Get ₹100 cashback"},
                                            "offerDescription": {
                                                "id": "TEST002",
                                                "text": "Test offer"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    
    # First request
    response1 = client.post("/offer", json=payload)
    assert response1.json()["noOfNewOffersCreated"] == 1
    
    # Second request - duplicate
    response2 = client.post("/offer", json=payload)
    assert response2.json()["noOfNewOffersCreated"] == 0
    assert response2.json()["noOfOffersIdentified"] == 1


def test_get_highest_discount():
    """Test getting highest discount"""
    # First create an offer
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["AXIS"],
                                            "offerText": {"text": "Get ₹100 cashback"},
                                            "offerDescription": {
                                                "id": "TEST003",
                                                "text": "Flat ₹100 cashback. Min Order ₹5000"
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "type": "PAYMENT_OPTION",
                            "data": {"instrumentType": "CREDIT"}
                        }
                    ]
                }
            }
        }
    }
    client.post("/offer", json=payload)
    
    # Get highest discount
    response = client.get("/highest-discount?amountToPay=10000&bankName=AXIS")
    assert response.status_code == 200
    data = response.json()
    assert data["highestDiscountAmount"] == 100.0


def test_get_highest_discount_with_payment_instrument():
    """Test highest discount with payment instrument filter"""
    # Create offer
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["HDFC"],
                                            "offerText": {"text": "Get ₹200 off"},
                                            "offerDescription": {
                                                "id": "TEST004",
                                                "text": "Flat ₹200 off"
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "type": "PAYMENT_OPTION",
                            "data": {"instrumentType": "CREDIT"}
                        }
                    ]
                }
            }
        }
    }
    client.post("/offer", json=payload)
    
    # Get with payment instrument
    response = client.get(
        "/highest-discount?amountToPay=10000&bankName=HDFC&paymentInstrument=CREDIT"
    )
    assert response.status_code == 200
    assert response.json()["highestDiscountAmount"] == 200.0


def test_get_highest_discount_nonexistent_bank():
    """Test getting discount for non-existent bank"""
    response = client.get("/highest-discount?amountToPay=10000&bankName=NONEXISTENT")
    assert response.status_code == 200
    assert response.json()["highestDiscountAmount"] == 0.0


def test_get_highest_discount_below_minimum():
    """Test discount when amount is below minimum"""
    # Create offer with min value
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["ICICI"],
                                            "offerText": {"text": "Get ₹500 off"},
                                            "offerDescription": {
                                                "id": "TEST005",
                                                "text": "Flat ₹500 off. Min Order ₹10000"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    client.post("/offer", json=payload)
    
    # Amount below minimum
    response = client.get("/highest-discount?amountToPay=5000&bankName=ICICI")
    assert response.status_code == 200
    assert response.json()["highestDiscountAmount"] == 0.0


def test_get_highest_discount_percentage_with_cap():
    """Test percentage discount with cap"""
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["SBI"],
                                            "offerText": {"text": "Get 5% cashback"},
                                            "offerDescription": {
                                                "id": "TEST006",
                                                "text": "5% cashback up to ₹500"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    client.post("/offer", json=payload)
    
    # 5% of 20000 = 1000, but capped at 500
    response = client.get("/highest-discount?amountToPay=20000&bankName=SBI")
    assert response.status_code == 200
    assert response.json()["highestDiscountAmount"] == 500.0


def test_get_all_offers():
    """Test getting all offers"""
    # Create some offers
    payload = {
        "flipkartOfferApiResponse": {
            "pageData": {
                "paymentOptions": {
                    "items": [
                        {
                            "type": "OFFER_LIST",
                            "data": {
                                "offers": {
                                    "offerList": [
                                        {
                                            "provider": ["AXIS"],
                                            "offerText": {"text": "Offer 1"},
                                            "offerDescription": {"id": "TEST007", "text": "Test"}
                                        },
                                        {
                                            "provider": ["HDFC"],
                                            "offerText": {"text": "Offer 2"},
                                            "offerDescription": {"id": "TEST008", "text": "Test"}
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    client.post("/offer", json=payload)
    
    response = client.get("/offers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["offers"]) == 2


def test_post_offer_empty_response():
    """Test posting empty offer response"""
    payload = {"flipkartOfferApiResponse": {}}
    
    response = client.post("/offer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["noOfOffersIdentified"] == 0
    assert data["noOfNewOffersCreated"] == 0