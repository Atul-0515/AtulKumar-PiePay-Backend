# Manual Testing Screenshots

All endpoints tested using Postman.

## POST /offer - Create Offers

**First Request (3 new offers created):**
![](screenshots/postman-create-offers-1.png)

**Second Request (0 new - duplicates prevented):**
![](screenshots/postman-create-offers-2.png)

## GET /highest-discount - Discount Calculations

**AXIS Bank @ ₹10,000 = ₹200:**
![](screenshots/postman-discount-axis-10k.png)

**AXIS Bank @ ₹6,000 = ₹100:**
![](screenshots/postman-discount-axis-6k.png)

**ICICI Bank @ ₹20,000 = ₹500 (capped):**
![](screenshots/postman-discount-icici-20k.png)

**With Payment Instrument (CREDIT):**
![](screenshots/postman-discount-with-instrument.png)

**Invalid Bank = ₹0:**
![](screenshots/postman-discount-invalid-bank.png)

## GET /offers - View All Offers

**All 14 offers listed:**
![](screenshots/postman-view-offers.png)
