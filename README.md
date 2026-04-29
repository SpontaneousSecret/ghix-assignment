# Career Relocation Planner

A full-stack web application that helps professionals plan international career relocations with data-driven insights and AI-generated guidance.

## Features

- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Relocation Plan Generation**: Generate detailed relocation plans based on destination data
- **Deterministic Checks**: Salary threshold validation, timeline conflict detection, missing data handling
- **AI Narratives**: LLM-generated guidance using Gemini Flash API (with fallback)
- **Data Confidence Tracking**: All responses include confidence indicators
- **Plan History**: Full audit trail of all user submissions
- **Mobile-Friendly API**: Clean, RESTful API design

## Tech Stack

### Backend
- **Flask** - Web framework
- **SQLAlchemy** - ORM and database management
- **SQLite** - Database (instance/career_relocation.db)
- **PyJWT** - JWT token authentication
- **bcrypt** - Password hashing
- **Gemini Flash** - LLM for narrative generation (via REST API)

### Frontend
- **Vanilla JavaScript** - No frameworks or build steps
- **HTML5/CSS3** - Single-page application with view switching
- **LocalStorage** - JWT token persistence

## Project Structure

```
ghix-assgnment/
├── app/
│   ├── __init__.py          # Flask app factory with blueprints
│   ├── models.py            # SQLAlchemy models (User, RelocationPlan)
│   ├── database.py          # Database CRUD operations
│   ├── config.py            # Configuration classes
│   ├── auth.py              # JWT authentication endpoints
│   ├── plans.py             # Relocation plan endpoints
│   ├── data_loader.py       # Deterministic validation functions
│   └── llm.py               # Gemini API integration
├── data/
│   ├── germany_senior_backend_engineer.json
│   └── uk_product_manager.json
├── instance/
│   └── career_relocation.db # SQLite database (auto-created)
├── index.html               # Single-page frontend
├── run.py                   # Flask application runner
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
python3 run.py
```

Backend will run on `http://localhost:5000`

### 3. Start the Frontend

```bash
python3 -m http.server 8080
```

Frontend will be available at `http://localhost:8080/index.html`

### 4. (Optional) Set Gemini API Key

For AI-generated narratives, set the environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
python3 run.py
```

Without the API key, the app uses a fallback narrative generator.

## API Endpoints

### Authentication

#### Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response: 201 Created
{
  "message": "User registered successfully",
  "token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in_hours": 24,
  "user": { ... }
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response: 200 OK
{
  "message": "Login successful",
  "token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in_hours": 24,
  "user": { ... }
}
```

### Plans (Requires Authentication)

#### Generate Plan
```bash
POST /api/plans/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "origin": "India",
  "destination": "Germany",
  "target_role": "Senior Backend Engineer",
  "salary_expectation": 45000,
  "currency": "EUR",
  "timeline_months": 12,
  "work_auth_constraint": "Need visa sponsorship"
}

Response: 201 Created
{
  "message": "Relocation plan generated successfully",
  "plan": { ... },
  "data_confidence": {
    "salary_data_available": true,
    "timeline_data_available": true,
    "visa_data_available": true,
    "overall_confidence": "medium"
  }
}
```

#### List All Plans
```bash
GET /api/plans?limit=10&offset=0
Authorization: Bearer <token>

Response: 200 OK
{
  "plans": [ ... ],
  "count": 5,
  "offset": 0,
  "limit": 10
}
```

#### Get Single Plan
```bash
GET /api/plans/<id>
Authorization: Bearer <token>

Response: 200 OK
{
  "plan": { ... }
}
```

## Critical Design Rules

### 1. Deterministic Checks Only
- LLM is **NEVER** used for eligibility, salary, or timeline logic
- All validation is deterministic in `app/data_loader.py`
- LLM is **ONLY** called after deterministic checks pass

### 2. Data Confidence
- All API responses include a `data_confidence` field
- Tracks availability of salary, timeline, and visa data
- Overall confidence: high/medium/low/none

### 3. Adding New Destinations
- Zero code changes required
- Simply add a JSON file: `data/{destination}_{role}.json`
- File naming: lowercase, underscores (e.g., `germany_senior_backend_engineer.json`)

### 4. Edge Case Handling
- **Timeline conflict**: Returns warning, doesn't reject
- **Salary shortfall**: Shows exact gap amount in warning
- **Missing data**: Returns structured error, NO LLM call

## Data File Structure

Example: `data/germany_senior_backend_engineer.json`

```json
{
  "destination": "Germany",
  "role": "Senior Backend Engineer",
  "visa_requirements": {
    "type": "EU Blue Card",
    "min_salary_threshold": 45552,
    "currency": "EUR",
    "sponsorship_available": true,
    "processing_time_months": 3
  },
  "timeline": {
    "min_months": 6,
    "typical_months": 9,
    "max_months": 12,
    "breakdown": {
      "job_search": "2-4 months",
      "interview_process": "1-2 months",
      "visa_processing": "2-3 months",
      "relocation": "1 month"
    }
  },
  "salary_data": {
    "min": 55000,
    "median": 75000,
    "max": 95000,
    "currency": "EUR"
  }
}
```

## Database Schema

### Users Table
- `id` (PRIMARY KEY)
- `email` (UNIQUE, INDEXED)
- `password_hash` (bcrypt)
- `created_at`
- `updated_at`

### RelocationPlans Table
- `id` (PRIMARY KEY)
- `user_id` (FOREIGN KEY → users.id, CASCADE DELETE)
- `origin`, `destination`, `target_role`
- `salary_expectation`, `currency`
- `timeline_months`
- `work_auth_constraint`
- `plan_json` (TEXT - full plan as JSON)
- `data_confidence_json` (TEXT - confidence flags)
- `generated_at` (INDEXED)

**History Tracking**: Each plan submission creates a NEW row (no updates)

## Frontend Views

1. **Auth View**: Login/Register with tabbed interface
2. **Generate Form**: Pre-filled with Scenario A defaults
3. **Result View**: Warnings, confidence badges, action steps, AI narrative
4. **Saved Plans**: Clickable cards showing all past plans

## Testing

### Manual Testing with curl

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 2. Login and get token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r '.token')

# 3. Generate plan
curl -X POST http://localhost:5000/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "origin": "India",
    "destination": "Germany",
    "target_role": "Senior Backend Engineer",
    "salary_expectation": 45000,
    "currency": "EUR",
    "timeline_months": 12,
    "work_auth_constraint": "Need visa sponsorship"
  }'

# 4. Test missing data error
curl -X POST http://localhost:5000/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "origin": "India",
    "destination": "Singapore",
    "target_role": "Software Engineer",
    "salary_expectation": 80000,
    "currency": "SGD",
    "timeline_months": 6,
    "work_auth_constraint": "Need visa"
  }'

# 5. Get all plans
curl -X GET http://localhost:5000/api/plans \
  -H "Authorization: Bearer $TOKEN"
```

## Configuration

### Development (Default)
```python
DEBUG = True
SQLALCHEMY_ECHO = True
DATABASE = sqlite:///instance/career_relocation.db
```

### Production
Set environment variables:
```bash
export JWT_SECRET_KEY="your-secret-key"
export SECRET_KEY="your-flask-secret"
export GEMINI_API_KEY="your-gemini-api-key"
```

## Security Features

- JWT tokens with 24-hour expiry
- Bcrypt password hashing (12 rounds)
- CSRF protection via JWT
- User ownership verification on plan access
- Cascade deletion (deleting user removes all plans)

## Performance Optimizations

- Database indexes on frequently queried fields
- Composite indexes for common query patterns
- Lazy loading for relationships
- JSON text storage for flexible plan data

## Error Handling

All endpoints return consistent error formats:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": []  // Optional additional info
}
```

## Future Enhancements

- Email verification for new users
- Password reset functionality
- Plan comparison feature
- Export plans to PDF
- More destination/role combinations
- Real-time collaboration
- Admin dashboard

## License

Private project - All rights reserved

## Support

For questions or issues, contact the development team.
