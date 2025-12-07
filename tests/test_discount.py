"""
Test suite for discount calculation logic
"""
import pytest
from app.utils import extract_discount_amount, calculate_discount


def test_extract_flat_discount():
    """Test extracting flat discount amounts"""
    assert extract_discount_amount("Get ₹100 cashback") == 100.0
    assert extract_discount_amount("Flat ₹500 off") == 500.0
    assert extract_discount_amount("Save ₹1000") == 1000.0
    assert extract_discount_amount("Get ₹50 off") == 50.0


def test_extract_percentage_discount():
    """Test extracting percentage discounts"""
    assert extract_discount_amount("Get 5% cashback") == 5.0
    assert extract_discount_amount("10% off") == 10.0
    assert extract_discount_amount("Save 15%") == 15.0


def test_extract_discount_with_comma():
    """Test extracting amounts with commas"""
    assert extract_discount_amount("Get ₹1,000 off") == 1000.0
    assert extract_discount_amount("Save ₹10,000") == 10000.0


def test_extract_discount_case_insensitive():
    """Test case variations"""
    assert extract_discount_amount("Up To ₹50 Cashback") == 50.0
    assert extract_discount_amount("FLAT ₹100 OFF") == 100.0


def test_extract_discount_no_match():
    """Test when no discount found"""
    assert extract_discount_amount("No cost EMI") == 0.0
    assert extract_discount_amount("") == 0.0
    assert extract_discount_amount("Some random text") == 0.0


def test_calculate_flat_discount():
    """Test flat discount calculation"""
    offer_text = "Get ₹100 cashback"
    offer_desc = "Flat ₹100 cashback. Min Order Value ₹5000"
    
    # Above minimum
    assert calculate_discount(offer_text, offer_desc, 10000) == 100.0
    
    # Below minimum
    assert calculate_discount(offer_text, offer_desc, 3000) == 0.0
    
    # Exactly at minimum
    assert calculate_discount(offer_text, offer_desc, 5000) == 100.0


def test_calculate_percentage_discount():
    """Test percentage discount calculation"""
    offer_text = "Get 5% cashback"
    offer_desc = "5% cashback on all orders"
    
    assert calculate_discount(offer_text, offer_desc, 10000) == 500.0
    assert calculate_discount(offer_text, offer_desc, 20000) == 1000.0
    assert calculate_discount(offer_text, offer_desc, 1000) == 50.0


def test_calculate_percentage_with_cap():
    """Test percentage discount with maximum cap"""
    offer_text = "Get 5% cashback"
    offer_desc = "5% cashback up to ₹500"
    
    # Below cap
    assert calculate_discount(offer_text, offer_desc, 5000) == 250.0
    
    # Above cap - should return cap amount
    assert calculate_discount(offer_text, offer_desc, 20000) == 500.0


def test_calculate_percentage_with_max_keyword():
    """Test percentage with 'maximum' keyword"""
    offer_text = "Get 10% off"
    offer_desc = "10% discount maximum ₹1000"
    
    assert calculate_discount(offer_text, offer_desc, 15000) == 1000.0


def test_calculate_with_min_order_value():
    """Test discount with minimum order value"""
    offer_text = "Get ₹200 off"
    offer_desc = "Flat ₹200 off. Minimum order value ₹10000"
    
    assert calculate_discount(offer_text, offer_desc, 15000) == 200.0
    assert calculate_discount(offer_text, offer_desc, 8000) == 0.0


def test_calculate_percentage_with_min_and_cap():
    """Test percentage with both min order and cap"""
    offer_text = "Get 5% cashback"
    offer_desc = "5% cashback upto ₹750. Min order ₹5000"
    
    # Above min, below cap
    assert calculate_discount(offer_text, offer_desc, 10000) == 500.0
    
    # Above min, above cap
    assert calculate_discount(offer_text, offer_desc, 20000) == 750.0
    
    # Below min
    assert calculate_discount(offer_text, offer_desc, 3000) == 0.0


def test_calculate_no_discount():
    """Test offers with no clear discount"""
    offer_text = "No cost EMI"
    offer_desc = "No Cost EMI available"
    
    assert calculate_discount(offer_text, offer_desc, 10000) == 0.0