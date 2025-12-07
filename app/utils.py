import re
from typing import List, Dict, Any, Optional, Tuple


def safe_get(data: Dict, *keys, default=None):
    """
    Safely navigate nested dictionary keys.
    Example: safe_get(data, 'pageData', 'paymentOptions', 'items')
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def extract_discount_amount(text: str) -> float:
    """
    Extract discount amount from offer text.
    Handles formats like:
    - "Get ₹10 cashback"
    - "Flat ₹50 off"
    - "Save ₹100"
    - "5% cashback"
    - "Up To ₹50 Cashback"
    Returns amount in rupees
    """
    if not text:
        return 0.0
    
    # Remove commas from numbers
    text = text.replace(',', '')
    
    # Pattern for fixed amount: ₹10, ₹50, ₹100, etc.
    rupee_pattern = r'₹\s*(\d+(?:\.\d+)?)'
    matches = re.findall(rupee_pattern, text)
    
    if matches:
        # Return the first match (usually the discount amount)
        return float(matches[0])
    
    # Pattern for percentage: 5%, 10%, etc.
    percent_pattern = r'(\d+(?:\.\d+)?)\s*%'
    percent_matches = re.findall(percent_pattern, text)
    
    if percent_matches:
        # For percentage offers, return the percentage value
        return float(percent_matches[0])
    
    return 0.0


def find_offer_list_items(data: Any, path: str = "root") -> List[Any]:
    """
    Recursively search for items array that contains OFFER_LIST type.
    This handles multiple possible JSON structures.
    """
    items_list = []
    
    if isinstance(data, dict):
        # Check if current dict has 'items' key
        if 'items' in data and isinstance(data['items'], list):
            # Check if any item is OFFER_LIST
            for item in data['items']:
                if isinstance(item, dict) and item.get('type') == 'OFFER_LIST':
                    items_list.extend(data['items'])
                    break
        
        # Recursively search in all dict values
        for key, value in data.items():
            items_list.extend(find_offer_list_items(value, f"{path}.{key}"))
    
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            items_list.extend(find_offer_list_items(item, f"{path}[{idx}]"))
    
    return items_list


def extract_offers_from_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract offer list from items array.
    Handles the offer structure extraction.
    """
    offers = []
    
    for item in items:
        if not isinstance(item, dict):
            continue
            
        # Check if this is an OFFER_LIST type
        if item.get('type') == 'OFFER_LIST':
            # Try multiple possible paths to offer list
            offer_list = (
                safe_get(item, 'data', 'offers', 'offerList') or
                safe_get(item, 'data', 'offerList') or
                safe_get(item, 'offers', 'offerList') or
                safe_get(item, 'offerList') or
                []
            )
            
            if isinstance(offer_list, list):
                offers.extend(offer_list)
    
    return offers


def extract_payment_instruments_from_response(flipkart_response: Dict[str, Any]) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Extract payment instruments from response.
    Returns: (offer_instrument_mapping, list_of_instruments)
    """
    offer_instrument_mapping = {}
    payment_instruments_found = set()
    
    try:
        items = safe_get(flipkart_response, 'pageData', 'paymentOptions', 'items')
        if not items:
            items = safe_get(flipkart_response, 'paymentOptions', 'items')
        if not items:
            items = safe_get(flipkart_response, 'items')
        
        if not items or not isinstance(items, list):
            return offer_instrument_mapping, []
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            if item.get('type') == 'PAYMENT_OPTION':
                instrument_type = safe_get(item, 'data', 'instrumentType')
                if instrument_type:
                    payment_instruments_found.add(instrument_type)
        
    except Exception as e:
        print(f"Error extracting payment instruments: {e}")
        return offer_instrument_mapping, []
    
    return offer_instrument_mapping, list(payment_instruments_found)


def parse_offers_from_flipkart_response(flipkart_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse offers from Flipkart's SSR response.
    Handles multiple possible JSON structures.
    """
    parsed_offers = []
    
    try:
        # Extract payment instruments
        _, available_instruments = extract_payment_instruments_from_response(flipkart_response)
        
        # Find items
        items = safe_get(flipkart_response, 'pageData', 'paymentOptions', 'items')
        if not items:
            items = safe_get(flipkart_response, 'paymentOptions', 'items')
        if not items:
            items = safe_get(flipkart_response, 'items')
        if not items:
            items = find_offer_list_items(flipkart_response)
        
        if not items or not isinstance(items, list):
            return parsed_offers
        
        # Extract offers
        offers = extract_offers_from_items(items)
        
        if not offers:
            return parsed_offers
        
        # Parse each offer
        for offer in offers:
            try:
                offer_id = (
                    safe_get(offer, 'offerDescription', 'id') or
                    safe_get(offer, 'id') or
                    safe_get(offer, 'offerId')
                )
                
                if not offer_id:
                    continue
                
                offer_text = (
                    safe_get(offer, 'offerText', 'text') or
                    safe_get(offer, 'offerText') or
                    safe_get(offer, 'text') or
                    ''
                )
                
                offer_description = (
                    safe_get(offer, 'offerDescription', 'text') or
                    safe_get(offer, 'description') or
                    safe_get(offer, 'offerDescription') or
                    ''
                )
                
                logo = safe_get(offer, 'logo', default='')
                
                providers = safe_get(offer, 'provider', default=[])
                bank_codes = [code for code in providers if code] if isinstance(providers, list) else []
                
                # Assign payment instruments if offer has banks
                payment_instruments = available_instruments.copy() if bank_codes and available_instruments else []
                
                parsed_offers.append({
                    'offer_id': offer_id,
                    'offer_text': offer_text,
                    'offer_description': offer_description,
                    'logo': logo,
                    'bank_codes': bank_codes,
                    'payment_instruments': payment_instruments
                })
                
            except Exception as e:
                print(f"Error parsing offer: {e}")
                continue
        
    except Exception as e:
        print(f"Error parsing response: {e}")
    
    return parsed_offers


def calculate_discount(offer_text: str, offer_description: str, amount_to_pay: float) -> float:
    """
    Calculate actual discount amount.
    """
    # Check minimum order value first (applies to all offers)
    min_pattern = r'(?:min|minimum).*?(?:order|value|booking).*?₹\s*(\d+(?:,\d+)?)'
    min_match = re.search(min_pattern, offer_description, re.IGNORECASE)
    
    if min_match:
        min_order_value = float(min_match.group(1).replace(',', ''))
        if amount_to_pay < min_order_value:
            return 0.0
    
    discount = extract_discount_amount(offer_text)
    
    # Check if percentage offer
    if '%' in offer_text:
        discount_amount = (discount / 100) * amount_to_pay
        
        # Check for max cap
        cap_pattern = r'(?:upto|up to|maximum|max)\s*₹\s*(\d+(?:,\d+)?)'
        cap_match = re.search(cap_pattern, offer_description, re.IGNORECASE)
        
        if cap_match:
            max_discount = float(cap_match.group(1).replace(',', ''))
            discount_amount = min(discount_amount, max_discount)
        
        return discount_amount
    
    # Return flat discount
    return discount