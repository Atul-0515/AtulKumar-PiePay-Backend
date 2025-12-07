# PiePay Backend - Flipkart Offer Detection Service

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)

Backend service to detect, store, and calculate best discounts from Flipkart offers.

## 🚀 Quick Start

### Prerequisites
- Python 3.10

### Setup & Run

```bash
# Clone and navigate
git clone https://github.com/Atul-0515/AtulKumar-PiePay-Backend.git
cd AtulKumar-PiePay-Backend

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

**Interactive API Docs**: `http://127.0.0.1:8000/docs`

## 🧪 Running Tests

### Install Test Dependencies

```bash
pip install pytest httpx
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_api.py::test_post_offer_success
```

### Test Coverage

The test suite includes:
- **Parser Tests** (`tests/test_parser.py`): Tests for JSON parsing with various structures
- **Discount Tests** (`tests/test_discount.py`): Tests for discount calculation logic
- **API Tests** (`tests/test_api.py`): Integration tests for all endpoints

**Expected Output:**
```
tests/test_parser.py::test_parse_direct_items PASSED                                                                                                  [ 83%]
tests/test_parser.py::test_parse_upi_offers_without_banks PASSED                                                                                      [ 86%]
tests/test_parser.py::test_parse_skip_offers_without_id PASSED                                                                                        [ 90%]
tests/test_parser.py::test_extract_payment_instruments PASSED                                                                                         [ 93%]
tests/test_parser.py::test_parse_empty_response PASSED                                                                                                [ 96%]
tests/test_parser.py::test_parse_multiple_offers PASSED                                                                                               [100%]
==================================================================== 30 passed in 0.58s =====================================================================
```

## 📚 API Endpoints

### POST /offer
Store offers from Flipkart response.

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/offer" \
  -H "Content-Type: application/json" \
  -d '{
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
                      "offerText": {"text": "Get ₹500 cashback"},
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
  }'
```

**Response:**
```json
{
  "noOfOffersIdentified": 1,
  "noOfNewOffersCreated": 1
}
```

### GET /highest-discount
Calculate best discount for payment details.

**Example Requests:**
```bash
# Basic
curl "http://127.0.0.1:8000/highest-discount?amountToPay=10000&bankName=AXIS"

# With payment instrument (Bonus Part 4)
curl "http://127.0.0.1:8000/highest-discount?amountToPay=10000&bankName=AXIS&paymentInstrument=CREDIT"
```

**Response:**
```json
{
  "highestDiscountAmount": 500.0
}
```

## 📊 Assumptions

1. **Flipkart Uses Server-Side Rendering (SSR)**: 
   - After inspecting Flipkart's payment page network activity, I found that **no separate API call is made to fetch offers**
   - Offers are embedded directly in the HTML within `window.__INITIAL_STATE__` JavaScript object
   - This is a common SSR pattern where data is serialized into the page during server rendering
   - Therefore, the JSON structure I'm parsing comes from this embedded data, not from a traditional REST API response
   - The `flipkartOfferApiResponse` in the POST request represents this extracted SSR data

2. **JSON Structure Flexibility**: The parser handles multiple possible structures since SSR data can vary:
   - `pageData.paymentOptions.items` (standard)
   - `paymentOptions.items` (simplified)
   - `items` (direct)
   - Uses recursive search as fallback for any nested structure

3. **Payment Instruments**: When CREDIT, EMI_OPTIONS, etc. are found in the response, they're associated with all bank offers. UPI-only offers (without banks) don't get payment instruments.

4. **Offer Uniqueness**: Identified by Flipkart's `offer_id`. Duplicate IDs are not re-inserted.

5. **Discount Calculation**:
   - **Flat offers** (e.g., "₹100 off"): Applied if minimum order value is met
   - **Percentage offers** (e.g., "5% cashback"): Calculated as `amount × percentage ÷ 100`, capped at maximum mentioned in description (e.g., "up to ₹500")

6. **Bank Codes**: Stored as-is from Flipkart (e.g., "AXIS", "FLIPKARTAXISBANK")

7. **Currency**: All amounts in INR (Indian Rupees)

## 🏗️ Design Choices

### Framework: FastAPI
**Why**: Automatic API docs, type validation with Pydantic, high performance, minimal boilerplate, excellent for rapid development within time constraints.

### Database: SQLite + SQLAlchemy
**Why**: 
- Zero configuration, serverless
- Perfect for development/testing
- Easy migration path to PostgreSQL for production
- All tables auto-created on startup (no manual migrations needed)

**Schema Design**:
- **offers**: Core offer data (id, offer_id, offer_text, offer_description, logo)
- **banks**: Bank information (id, bank_code)
- **payment_instruments**: Payment types (id, instrument_type)
- **Many-to-many**: One offer → multiple banks, one offer → multiple instruments

**Why this schema**: Normalized to avoid duplication, indexed for fast queries, supports complex relationships required by Flipkart's offer structure.

### JSON Parser Strategy
**Multi-layered approach**:
1. **Fast path**: Check common structures first (O(1))
2. **Recursive fallback**: Search entire JSON tree if needed
3. **Robust extraction**: Multiple fallback paths for each field
4. **Error isolation**: Each offer parsed independently, failures don't break batch

**Why**: Handles Flipkart's varying response formats without breaking. Future-proof against structure changes.

### Discount Calculation
Uses regex to extract:
- Fixed amounts: `₹\s*(\d+)`
- Percentages: `(\d+)\s*%`
- Max caps: `up to ₹(\d+)`
- Min order: `min.*?₹(\d+)`

Then applies business logic (percentage calculation, cap limits, minimum checks) and returns the highest applicable discount.

## 🚀 Scaling to 1,000 RPS

### Current Bottlenecks
- Database queries on every request
- Single instance deployment
- No caching

### Scaling Strategy

**1. Caching (Redis)**
```python
# Cache offer queries by bank+instrument for 5 minutes
cache_key = f"offers:{bank}:{instrument}"
# Expected: 95%+ cache hit rate, ~2ms latency
```

**2. Database Optimization**
- Add indexes on `bank_code`, `instrument_type`, `offer_id`
- Connection pooling (pool_size=20, max_overflow=40)
- Switch to PostgreSQL with read replicas for production

**3. Horizontal Scaling**
- Deploy 4 instances behind load balancer (Nginx/AWS ALB)
- Each instance handles ~250 RPS
- Kubernetes for auto-scaling

**4. Async Implementation**
- Convert to async/await for non-blocking I/O
- Use `databases` library for async SQLAlchemy

**5. Pre-computation**
- Pre-calculate discounts for common amounts (₹1K, ₹5K, ₹10K, etc.) and popular banks
- Store in cache, refresh hourly

### Expected Performance
- **With caching**: ~10ms latency, 1200+ RPS with 4 instances
- **Cost**: ~$200-300/month (AWS: 4 instances + Redis + PostgreSQL)

### Monitoring
- Track: Request latency (p95), cache hit rate, DB query time
- Auto-scale when CPU > 70% or latency > 100ms

## 💡 Future Improvements

**If I had more time:**

1. **Testing**: Unit tests for parser/calculator, integration tests for API, load testing with Locust

2. **Advanced Parsing**: Handle date ranges, user eligibility, offer stacking rules, tiered discounts

3. **Security**: API key auth, rate limiting (100 req/min per client), input sanitization

4. **Observability**: Structured logging (JSON), distributed tracing (OpenTelemetry), metrics dashboard (Grafana)

5. **API Features**: Pagination, filtering by bank/discount, sorting, offer history tracking

6. **Database**: Alembic migrations for version control, automated backups

7. **DevOps**: Docker containerization, CI/CD pipeline, blue-green deployments

8. **Error Handling**: Specific error codes, detailed messages, retry logic with circuit breaker

---

## 👤 Author

**[ATUL KUMAR / 22BTB0A40]**

**Status**: All requirements completed (Parts 1-4) ✅  

---

*This project is for educational/evaluation purposes only.*
