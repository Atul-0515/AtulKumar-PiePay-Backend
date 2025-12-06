# PiePay Backend - Flipkart Offer Detection Service

A FastAPI-based backend service that detects, stores, and analyzes offers from Flipkart's payment page to calculate the best discount for users.

## 🚀 Features

- **Bulletproof JSON Parsing**: Handles multiple Flipkart response structures gracefully
- **Offer Storage**: Stores offers with associated banks and payment instruments
- **Discount Calculation**: Calculates highest discount based on payment details
- **Duplicate Prevention**: Automatically prevents duplicate offer entries
- **Payment Instrument Support**: Full support for CREDIT, EMI_OPTIONS, and other payment types (Bonus Part 4)

## 📋 Prerequisites

- Python 3.10
- pip (Python package manager)

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd piepay-backend
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python -m uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

### 5. Access API Documentation

Open your browser and visit:
- Interactive Docs: `http://127.0.0.1:8000/docs`
- Root Endpoint: `http://127.0.0.1:8000`

## 📚 API Endpoints

### 1. POST /offer

Store offers from Flipkart's offer API response.

**Request:**
```json
{
  "flipkartOfferApiResponse": {
    "pageData": {
      "paymentOptions": {
        "items": [...]
      }
    }
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

### 2. GET /highest-discount

Calculate the highest discount for given payment details.

**Query Parameters:**
- `amountToPay` (required): Total amount to pay in rupees
- `bankName` (required): Bank code (e.g., AXIS, HDFC, ICICI)
- `paymentInstrument` (optional): Payment type (e.g., CREDIT, EMI_OPTIONS)

**Example:**
```bash
GET /highest-discount?amountToPay=10000&bankName=AXIS&paymentInstrument=CREDIT
```

**Response:**
```json
{
  "highestDiscountAmount": 500.0
}
```

### 3. GET /offers (Debug Endpoint)

View all stored offers.

### 4. DELETE /offers (Debug Endpoint)

Delete all offers (useful for testing).

## 🧪 Testing

### Run Parser Tests
```bash
python test_datasets.py
```

### Run CRUD Tests
```bash
python test_crud.py
```

### Run API Tests
```bash
python test_api.py
```

### Test with Real Flipkart Data
```bash
python test_real_flipkart.py
```

## 🏗️ Architecture & Design Choices

### Database Schema

**Tables:**
1. **offers**: Stores offer details (ID, text, description, logo)
2. **banks**: Stores bank codes (AXIS, HDFC, etc.)
3. **payment_instruments**: Stores payment types (CREDIT, EMI_OPTIONS, etc.)
4. **Association tables**: Many-to-many relationships between offers-banks and offers-instruments

**Why SQLite?**
- Lightweight and serverless
- Perfect for development and testing
- Easy to deploy
- Can be easily migrated to PostgreSQL for production

### Framework Choice: FastAPI

**Reasons:**
- Fast and modern Python web framework
- Automatic API documentation (Swagger UI)
- Type validation with Pydantic
- Async support for scalability
- Excellent developer experience

### JSON Parsing Strategy

The parser uses a **multi-strategy approach**:

1. **Fast Path**: Tries common JSON structures first
   - `pageData.paymentOptions.items`
   - `paymentOptions.items`
   - Direct `items` array

2. **Fallback**: Recursive search for OFFER_LIST items

3. **Robust Extraction**: Multiple fallback paths for each field
   - Handles missing fields gracefully
   - Skips malformed offers without crashing
   - Logs warnings for debugging

This approach ensures the parser works with various Flipkart response formats without breaking.

## 📊 Assumptions Made

1. **Payment Instrument Mapping**: When a bank offer is present and payment instruments are detected in the response, we associate all available payment instruments with bank offers. UPI offers (without provider banks) don't get payment instruments assigned.

2. **Offer Uniqueness**: Offers are uniquely identified by Flipkart's `offer_id`. Duplicate offers (same ID) are not inserted again.

3. **Discount Calculation**: 
   - For percentage offers: Calculate percentage of `amountToPay` and apply max cap if mentioned
   - For flat offers: Check minimum order value requirement
   - Amount is in rupees (not paise)

4. **Bank Code Format**: Bank codes are stored as-is from Flipkart (e.g., "AXIS", "FLIPKARTAXISBANK")

5. **Offer Expiry**: The system doesn't track offer expiry dates (not provided in the sample data)

## 🚀 Scaling GET /highest-discount to Handle 1,000 RPS

### Current Bottlenecks
- Database queries for each request
- Discount calculation logic runs for each offer

### Scaling Strategy

#### 1. **Database Optimization**
```python
# Add indexes
CREATE INDEX idx_bank_code ON banks(bank_code);
CREATE INDEX idx_instrument_type ON payment_instruments(instrument_type);
CREATE INDEX idx_offer_id ON offers(offer_id);
```

#### 2. **Caching Layer (Redis)**
```python
# Cache offer queries by bank + instrument
# TTL: 5 minutes (offers don't change frequently)
cache_key = f"offers:{bank_name}:{payment_instrument}"
offers = redis.get(cache_key)
if not offers:
    offers = db.query(...)
    redis.setex(cache_key, 300, offers)
```

#### 3. **Database Connection Pooling**
```python
# Use connection pooling to handle concurrent requests
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

#### 4. **Horizontal Scaling**
- Deploy multiple API instances behind a load balancer (Nginx/AWS ALB)
- Stateless architecture allows easy horizontal scaling
- Use managed database (AWS RDS, Google Cloud SQL) for better performance

#### 5. **Async Processing**
```python
# Convert to async for non-blocking I/O
@app.get("/highest-discount")
async def get_highest_discount(...):
    offers = await get_offers_async(...)
```

#### 6. **Pre-compute Common Scenarios**
- Pre-calculate discount amounts for common order values (₹1000, ₹5000, ₹10000, etc.)
- Store in cache for instant retrieval

#### 7. **Database Choice for Production**
- Switch to PostgreSQL for better concurrent read performance
- Use read replicas for query distribution
- Consider Amazon Aurora for auto-scaling

#### 8. **Monitoring & Optimization**
- Add APM tools (New Relic, DataDog)
- Monitor slow queries
- Add rate limiting to prevent abuse

**Expected Performance:**
- With caching: ~10ms response time
- Without caching: ~50-100ms response time
- Can handle 1000+ RPS with 3-4 instances

## 💡 Future Improvements

Given more time, I would improve:

1. **Advanced Offer Matching**
   - Parse offer terms more intelligently (date ranges, user eligibility)
   - Handle complex offer combinations
   - Support offer stacking rules

2. **Better Payment Instrument Detection**
   - More sophisticated logic to match specific offers to specific instruments
   - Handle EMI tenor-based offers
   - Support cashback vs instant discount differentiation

3. **Data Validation**
   - Add more comprehensive input validation
   - Validate bank codes against a whitelist
   - Sanitize and validate amounts

4. **Error Handling**
   - More granular error codes
   - Better error messages for clients
   - Retry logic for database failures

5. **Testing**
   - Add unit tests for all functions
   - Integration tests for API endpoints
   - Load testing with locust/k6

6. **Logging & Monitoring**
   - Structured logging (JSON format)
   - Request tracking with correlation IDs
   - Metrics for offer parsing success rate

7. **API Enhancements**
   - Pagination for GET /offers
   - Filtering options (by bank, by discount type)
   - Bulk offer deletion with filters
   - Offer history/versioning

8. **Security**
   - API key authentication
   - Rate limiting per client
   - Input sanitization for SQL injection prevention
   - CORS configuration

9. **Database Migrations**
   - Use Alembic for database migrations
   - Version control for schema changes

10. **Performance**
    - Implement GraphQL for flexible queries
    - Add database query result caching
    - Optimize discount calculation algorithm

## 📝 Notes

- This project uses Flipkart's offer API structure purely for evaluation purposes
- The parser is designed to be bulletproof and handle various JSON structures
- All amounts are in Indian Rupees (INR)
- The system automatically prevents duplicate offers based on offer_id

## 👤 Author

**Your Name/Roll Number**

## 📄 License

This project is for assignment/evaluation purposes.