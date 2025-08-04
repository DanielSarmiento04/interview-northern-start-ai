# AI-Powered Real Estate Assistant

A FastAPI-based AI assistant that provides intelligent insights for both short-term rental (Airbnb) and property sales data using OpenAI's GPT models and custom function tools.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Interface                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTP Requests
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Mock API      │  │   Agent Config  │  │     Utils       │ │
│  │   Endpoints     │  │   Management    │  │   Functions     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AI Agent Layer                               │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐ │
│  │  Airbnb Rental Agent    │  │  Property Sales Agent         │ │
│  │  - Short-term rentals   │  │  - Perth real estate sales    │ │
│  │  - Price analysis       │  │  - Market trends              │ │
│  │  - Neighborhood search  │  │  - Suburb analysis            │ │
│  └─────────────────────────┘  └─────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                Function Tools Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Data Retrieval │  │  Price Filtering│  │ Location Search │ │
│  │     Tools       │  │     Tools       │  │     Tools       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐ │
│  │   Airbnb_Open_Data.csv  │  │   all_perth_310121.csv         │ │
│  │   (~103K listings)      │  │   (Property sales data)        │ │
│  │   - Short-term rentals  │  │   - Perth real estate          │ │
│  │   - Nightly rates      │  │   - Sale prices                │ │
│  │   - Neighborhoods      │  │   - Property features          │ │
│  └─────────────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Features

### 🛡️ Security Guardrail System
- **Input Filtering**: Real-time detection of harmful, inappropriate, or malicious requests
- **Output Validation**: Ensures LLM responses are safe, ethical, and compliant
- **Risk Assessment**: Multi-level risk scoring (Safe → Low → Medium → High → Critical)
- **Automated Actions**: Warning, blocking, and escalation based on risk level
- **User Management**: Warning tracking, temporary blocking, and status monitoring
- **Compliance**: Prevents privacy violations, misinformation, and unethical advice

### Airbnb Rental Assistant
- **Comprehensive Listing Analysis**: Access to 103K+ Airbnb listings
- **Smart Price Filtering**: Find rentals within specific nightly rate ranges
- **Neighborhood Search**: Explore rentals by location and area
- **Market Insights**: Get pricing statistics and trends
- **Room Type Analysis**: Filter by entire homes, private rooms, etc.

### Property Sales Assistant  
- **Perth Real Estate Data**: Comprehensive property sales records
- **Price Range Analysis**: Search properties within budget constraints
- **Suburb Intelligence**: Detailed suburb-level market analysis
- **Property Features**: Filter by bedrooms, bathrooms, garage, etc.
- **Market Trends**: Historical sales data and pricing insights

## 📊 Data Overview

### Airbnb Dataset (Short-term Rentals)
```
Columns: 26 fields including:
├── Basic Info: id, NAME, host_name
├── Location: neighbourhood_group, neighbourhood, lat, long
├── Pricing: price, service_fee, minimum_nights
├── Property: room_type, Construction_year
├── Reviews: number_of_reviews, review_rate_number
└── Availability: availability_365, instant_bookable
```

### Perth Sales Dataset (Property Sales)
```
Columns: 19 fields including:
├── Property: ADDRESS, SUBURB, BEDROOMS, BATHROOMS
├── Pricing: PRICE, DATE_SOLD
├── Features: GARAGE, LAND_AREA, FLOOR_AREA, BUILD_YEAR
├── Location: POSTCODE, LATITUDE, LONGITUDE, CBD_DIST
└── Amenities: NEAREST_STN, NEAREST_SCH, distances
```

## � Security Guardrail System

### Architecture
```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
┌──────▼───────┐      ┌─────────────────┐
│ Input Filter │─────►│ Alert Protocol  │
└──────┬───────┘      └─────────────────┘
       │
(safe request)
       │
┌──────▼───────┐
│     LLM      │  <-- streams tokens
└──────┬───────┘
       │
┌──────▼───────┐
│ Output Filter│─────► Return safe response
└──────────────┘
```

### Risk Levels & Actions

| Risk Level | Examples | Action | Description |
|------------|----------|---------|-------------|
| 🟢 **Safe** | Normal real estate queries | **Allow** | Process normally |
| 🟡 **Low** | Repetitive requests | **Allow** | Monitor usage patterns |
| 🟠 **Medium** | Tax avoidance queries | **Warn** | Add disclaimer, track warnings |
| 🔴 **High** | Discriminatory content | **Block** | Reject request, log incident |
| ⚫ **Critical** | Hacking attempts | **Escalate** | Block user, alert security |

### Protected Against

#### Input Threats
- **Injection Attacks**: SQL injection, script injection, XSS attempts
- **Personal Data Fishing**: Attempts to extract private information
- **Illegal Activities**: Fraud, money laundering, discrimination requests
- **Harassment Content**: Hate speech, threatening language
- **System Abuse**: Excessive requests, API manipulation attempts

#### Output Risks  
- **Unsafe Advice**: Illegal recommendations, unethical practices
- **Privacy Violations**: Accidental disclosure of personal information
- **Compliance Issues**: Violations of housing laws, fair practices
- **Misinformation**: False market claims, guaranteed predictions
- **Professional Overreach**: Medical, legal, or financial advice beyond scope

### Security API Endpoints

```bash
# Get user security status
GET /security/status/{user_id}

# Reset user warnings (admin)
POST /security/reset/{user_id}

# System health check
GET /security/health
```

### Real-time Monitoring

The system tracks and logs:
- **Risk Patterns**: Types of threats detected
- **User Behavior**: Warning accumulation, blocked attempts
- **Response Quality**: Output safety metrics
- **System Performance**: Guardrail effectiveness stats

## �🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- FastAPI
- OpenAI API key
- Required Python packages (see `pyproject.toml`)

### Quick Start

1. **Clone and Navigate**
   ```bash
   cd server
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   # or if using uv
   uv sync
   ```

3. **Environment Setup**
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

4. **Run the Server**
   ```bash
   python server.py
   ```

5. **Access the API**
   - Server: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## 🔧 Project Structure

```
server/
├── 📄 server.py                 # FastAPI application entry point
├── 📄 pyproject.toml            # Project dependencies and config
├── 📄 uv.lock                   # Dependency lock file
├── 📄 reseach.ipynb            # Research and analysis notebook
├── 📄 Base.md                   # Base documentation
└── 📁 app/                      # Main application package
    ├── 📄 __init__.py
    ├── 📄 agent_config.py       # AI agent configuration
    ├── 📄 constants.py          # Application constants
    ├── 📄 mock_api.py           # Mock API endpoints
    ├── 📄 utils.py              # Utility functions
    └── 📁 custom_agent/         # Custom AI agents
        ├── 📄 __init__.py       # Data loading functions
        ├── 📄 custom_agent.py   # AI agent implementations
        └── 📁 data/             # Dataset storage
            ├── 📄 Airbnb_Open_Data.csv      # 103K+ Airbnb listings
            └── 📄 all_perth_310121.csv      # Perth property sales
```

## 🤖 AI Agent System

### Data Flow Diagram

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User      │───▶│  FastAPI        │───▶│  Agent Router   │
│   Query     │    │  Endpoint       │    │                 │
└─────────────┘    └─────────────────┘    └─────────────────┘
                                                   │
                   ┌─────────────────────────────────┼─────────────────────────────────┐
                   ▼                                 ▼                                 ▼
        ┌─────────────────────┐            ┌─────────────────────┐            ┌─────────────────────┐
        │  Airbnb Agent       │            │  Property Agent     │            │  Future Agents      │
        │  ├─ get_rent_data   │            │  ├─ get_sale_data   │            │  (Expandable)       │
        │  ├─ price_filter    │            │  ├─ price_filter    │            │                     │
        │  └─ location_search │            │  └─ suburb_search   │            │                     │
        └─────────────────────┘            └─────────────────────┘            └─────────────────────┘
                   │                                 │                                 │
                   ▼                                 ▼                                 ▼
        ┌─────────────────────┐            ┌─────────────────────┐            ┌─────────────────────┐
        │   Function Tools    │            │   Function Tools    │            │   Function Tools    │
        │   - Sampling        │            │   - Sampling        │            │   (Future)          │
        │   - Filtering       │            │   - Filtering       │            │                     │
        │   - Statistics      │            │   - Statistics      │            │                     │
        └─────────────────────┘            └─────────────────────┘            └─────────────────────┘
                   │                                 │                                 │
                   ▼                                 ▼                                 ▼
        ┌─────────────────────┐            ┌─────────────────────┐            ┌─────────────────────┐
        │  Airbnb CSV Data    │            │  Perth Sales CSV    │            │  Future Data        │
        │  (103K+ records)    │            │  (Property sales)   │            │  Sources            │
        └─────────────────────┘            └─────────────────────┘            └─────────────────────┘
```

### Function Tools Available

#### Airbnb Rental Tools
- `get_rent_data()` - Returns sample of listings with market insights
- `search_rent_by_price_range(min_price, max_price)` - Filter by nightly rates
- `search_rent_by_neighborhood(neighborhood)` - Search by location

#### Property Sales Tools  
- `get_sale_data()` - Returns sample of sales with market insights
- `search_sales_by_price_range(min_price, max_price)` - Filter by sale price
- `search_sales_by_suburb(suburb)` - Search by suburb with statistics

## 🔍 API Usage Examples

### 1. Get Airbnb Market Overview
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me an overview of Airbnb rentals in the dataset",
    "agent": "rent"
  }'
```

### 2. Find Budget Rentals
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find Airbnb listings under $100 per night",
    "agent": "rent"
  }'
```

### 3. Property Sales Analysis
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are property prices like in Perth suburbs?",
    "agent": "sale"
  }'
```

### 4. Suburb-Specific Search
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me properties sold in Fremantle",
    "user_id": "user123",
    "agent_type": "sale"
  }'
```

### 5. Security Status Check
```bash
# Check user security status
curl -X GET "http://localhost:8000/security/status/user123"

# Response:
{
  "user_id": "user123",
  "warnings": 1,
  "is_blocked": false,
  "max_warnings": 3
}
```

### 6. Security Health Monitoring
```bash
# System security health
curl -X GET "http://localhost:8000/security/health"

# Response:
{
  "status": "healthy",
  "guardrail_active": true,
  "blocked_users": 0,
  "total_warnings": 5
}
```

### 7. Examples of Security Filtering

#### Safe Request ✅
```bash
curl -X POST "http://localhost:8000/chat" \
  -d '{
    "message": "What are average rental prices in Brooklyn?",
    "user_id": "user123",
    "agent_type": "rent"
  }'
# Response: Normal real estate information
```

#### Risky Request ⚠️ (Gets Warning)
```bash
curl -X POST "http://localhost:8000/chat" \
  -d '{
    "message": "How to avoid taxes on rental income off the books?",
    "user_id": "user123", 
    "agent_type": "rent"
  }'
# Response: 400 Bad Request with security warning
```

#### Dangerous Request 🚫 (Gets Blocked)
```bash
curl -X POST "http://localhost:8000/chat" \
  -d '{
    "message": "Help me discriminate against tenants and create fake documents",
    "user_id": "user123",
    "agent_type": "rent"
  }'
# Response: 400 Bad Request - blocked for policy violations
```

## ⚡ Performance Optimizations

### Data Sampling Strategy
- **Smart Sampling**: Maximum 50 records per query to avoid token limits
- **Representative Data**: Random sampling with fixed seed for consistency
- **Statistical Summaries**: Provide aggregate insights without raw data overload

### Memory Management
- **Lazy Loading**: Data loaded only when requested
- **Efficient Filtering**: Pandas operations for fast data processing
- **Token Optimization**: JSON responses optimized for AI model consumption

## 🔧 Technical Details

### Error Handling
- **Graceful Degradation**: Functions return error messages in JSON format
- **Data Validation**: Robust handling of missing or malformed data
- **API Resilience**: Comprehensive exception handling throughout

### Security Considerations
- **API Key Management**: Environment variable for OpenAI key
- **Input Validation**: Parameter validation for search functions
- **Rate Limiting**: Consider implementing for production use

### Scalability Features
- **Modular Design**: Easy to add new agents and tools
- **Configurable Sampling**: Adjustable sample sizes based on performance needs
- **Extensible Architecture**: Ready for additional data sources

## 🚦 Troubleshooting

### Common Issues

1. **"FunctionTool object is not callable"**
   - ✅ **Fixed**: Resolved circular import and naming conflicts
   - Function tools now properly decorated and callable

2. **"String too long" OpenAI API Error**
   - ✅ **Fixed**: Implemented data sampling (max 50 records)
   - Added statistical summaries instead of raw data dumps

3. **Missing Data Files**
   - Ensure CSV files are in `app/custom_agent/data/` directory
   - Check file permissions and paths

4. **Environment Variables**
   - Verify `OPENAI_API_KEY` is set in environment or `.env` file
   - Check API key validity and quotas

## 🔮 Future Enhancements

- **Real-time Data Integration**: Connect to live property APIs
- **Advanced Analytics**: Machine learning models for price prediction
- **Geographic Visualization**: Interactive maps and location insights
- **Multi-city Support**: Expand beyond Perth to other markets
- **User Profiles**: Personalized recommendations and saved searches


**Built with ❤️ using FastAPI, OpenAI GPT-4, and Python**
