"""
Test suite for JSON parser
Tests various Flipkart response structures
"""
import pytest
from app.utils import parse_offers_from_flipkart_response, extract_payment_instruments_from_response


def test_parse_full_nested_structure():
    """Test standard Flipkart SSR structure"""
    data = {
        "pageData": {
            "paymentOptions": {
                "items": [
                    {
                        "type": "OFFER_LIST",
                        "data": {
                            "offers": {
                                "offerList": [
                                    {
                                        "provider": ["AXIS", "HDFC"],
                                        "logo": "https://example.com/axis.svg",
                                        "offerText": {"text": "Get ₹100 cashback"},
                                        "offerDescription": {
                                            "id": "FPO001",
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
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 1
    assert offers[0]['offer_id'] == 'FPO001'
    assert offers[0]['offer_text'] == 'Get ₹100 cashback'
    assert offers[0]['bank_codes'] == ['AXIS', 'HDFC']
    assert 'CREDIT' in offers[0]['payment_instruments']


def test_parse_simplified_structure():
    """Test simplified structure without pageData wrapper"""
    data = {
        "paymentOptions": {
            "items": [
                {
                    "type": "OFFER_LIST",
                    "data": {
                        "offers": {
                            "offerList": [
                                {
                                    "provider": ["SBI"],
                                    "offerText": {"text": "Save ₹200"},
                                    "offerDescription": {
                                        "id": "FPO002",
                                        "text": "Flat ₹200 off"
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 1
    assert offers[0]['offer_id'] == 'FPO002'
    assert offers[0]['bank_codes'] == ['SBI']


def test_parse_direct_items():
    """Test direct items array structure"""
    data = {
        "items": [
            {
                "type": "OFFER_LIST",
                "data": {
                    "offerList": [
                        {
                            "provider": ["ICICI"],
                            "offerText": {"text": "Get 5% cashback"},
                            "offerDescription": {
                                "id": "FPO003",
                                "text": "5% cashback up to ₹500"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 1
    assert offers[0]['offer_id'] == 'FPO003'


def test_parse_upi_offers_without_banks():
    """Test UPI offers that have no bank providers"""
    data = {
        "pageData": {
            "paymentOptions": {
                "items": [
                    {
                        "type": "OFFER_LIST",
                        "data": {
                            "offers": {
                                "offerList": [
                                    {
                                        "provider": [],
                                        "offerText": {"text": "Get ₹10 cashback"},
                                        "offerDescription": {
                                            "id": "FPO004",
                                            "text": "UPI cashback"
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
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 1
    assert offers[0]['bank_codes'] == []
    assert offers[0]['payment_instruments'] == []


def test_parse_skip_offers_without_id():
    """Test that offers without ID are skipped"""
    data = {
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
                                        "offerText": {"text": "Valid offer"},
                                        "offerDescription": {
                                            "id": "FPO005",
                                            "text": "Valid"
                                        }
                                    },
                                    {
                                        "provider": ["HDFC"],
                                        "offerText": {"text": "No ID offer"},
                                        "offerDescription": {
                                            "text": "Should be skipped"
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
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 1
    assert offers[0]['offer_id'] == 'FPO005'


def test_extract_payment_instruments():
    """Test payment instrument extraction"""
    data = {
        "pageData": {
            "paymentOptions": {
                "items": [
                    {"type": "PAYMENT_OPTION", "data": {"instrumentType": "CREDIT"}},
                    {"type": "PAYMENT_OPTION", "data": {"instrumentType": "EMI_OPTIONS"}},
                    {"type": "PAYMENT_OPTION", "data": {"instrumentType": "UPI"}}
                ]
            }
        }
    }
    
    _, instruments = extract_payment_instruments_from_response(data)
    
    assert len(instruments) == 3
    assert "CREDIT" in instruments
    assert "EMI_OPTIONS" in instruments
    assert "UPI" in instruments


def test_parse_empty_response():
    """Test parsing empty response"""
    offers = parse_offers_from_flipkart_response({})
    assert offers == []


def test_parse_multiple_offers():
    """Test parsing multiple offers"""
    data = {
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
                                        "offerDescription": {"id": "FPO001", "text": "Text 1"}
                                    },
                                    {
                                        "provider": ["HDFC"],
                                        "offerText": {"text": "Offer 2"},
                                        "offerDescription": {"id": "FPO002", "text": "Text 2"}
                                    },
                                    {
                                        "provider": ["ICICI"],
                                        "offerText": {"text": "Offer 3"},
                                        "offerDescription": {"id": "FPO003", "text": "Text 3"}
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }
    
    offers = parse_offers_from_flipkart_response(data)
    
    assert len(offers) == 3
    assert offers[0]['offer_id'] == 'FPO001'
    assert offers[1]['offer_id'] == 'FPO002'
    assert offers[2]['offer_id'] == 'FPO003'