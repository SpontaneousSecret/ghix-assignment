# Career Relocation Planner

AI-powered international career relocation planning with deterministic validation and data confidence tracking.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start PostgreSQL and create the database
createdb career_relocation

# 3. Set environment variables (or create a .env file)
GROQ_API_KEY=your-groq-api-key


# 4. Start the server
python3 run.py
```

Server runs on http://localhost:8006

serve with `python3 -m http.server 8080`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Optional | Groq API key for AI narratives. Falls back to template narrative if absent. |

`.env` file example:
```
GROQ_API_KEY=gsk_...

```

---

## Evaluation Scenarios

### Scenario A: India → Germany (Senior Backend Engineer)

**Expected behavior**: Salary shortfall warning (EUR 45,000 vs EUR 45,552 threshold)

```bash
# Register user
curl -X POST http://localhost:8006/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"scenario_a@test.com","password":"password123"}'

# Login and save token
curl -X POST http://localhost:8006/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"scenario_a@test.com","password":"password123"}' \
  | jq -r '.token' > /tmp/token_a.txt

# Generate Plan A
curl -X POST http://localhost:8006/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat /tmp/token_a.txt)" \
  -d '{
    "origin": "India",
    "destination": "Germany",
    "target_role": "Senior Backend Engineer",
    "salary_expectation": 45000,
    "currency": "EUR",
    "timeline_months": 12,
    "work_auth_constraint": "Need visa sponsorship"
  }'
```

**Key assertions:**
- `data_confidence.overall_confidence` = "medium" (due to salary warning)
- `plan.plan.warnings` contains salary shortfall of EUR 552
- `plan.plan.eligibility.visa_type` = "EU Blue Card"
- `plan.plan.eligibility.min_salary_threshold` = 45552

---

### Scenario B: India → UK (Product Manager)

**Expected behavior**: No warnings (salary exceeds threshold), different visa type

```bash
curl -X POST http://localhost:8006/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"scenario_b@test.com","password":"password123"}' \
  | jq -r '.token' > /tmp/token_b.txt

curl -X POST http://localhost:8006/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(cat /tmp/token_b.txt)" \
  -d '{
    "origin": "India",
    "destination": "UK",
    "target_role": "Product Manager",
    "salary_expectation": 50000,
    "currency": "GBP",
    "timeline_months": 8,
    "work_auth_constraint": "Need visa sponsorship"
  }'
```

**Key assertions:**
- `data_confidence.overall_confidence` = "high" (no warnings)
- `plan.plan.warnings` = [] (empty array)
- `plan.plan.eligibility.visa_type` = "Skilled Worker Visa"
- `plan.plan.eligibility.min_salary_threshold` = 38700
- `plan.plan.timeline.typical_timeline_months` = 8

---

## Adding New Destinations

Drop a JSON file in `data/` following this naming convention:

```
data/{destination}_{role}.json
```

Example: `data/canada_software_engineer.json`

```json
{
  "destination": "Canada",
  "role": "Software Engineer",
  "visa_requirements": {
    "type": "Express Entry",
    "min_salary_threshold": 60000,
    "currency": "CAD",
    "sponsorship_available": true,
    "processing_time_months": 6
  },
  "timeline": {
    "min_months": 8,
    "typical_months": 12,
    "max_months": 18,
    "breakdown": {
      "job_search": "3-5 months",
      "interview_process": "1-2 months",
      "visa_processing": "4-6 months",
      "relocation": "1 month"
    }
  },
  "salary_data": {
    "min": 70000,
    "median": 95000,
    "max": 130000,
    "currency": "CAD"
  }
}
```

**No code changes required** — restart the server and the new destination is available.

Destinations without a JSON file still work: the app uses global estimates and marks data as "Estimated" rather than "Verified".

---

## API Endpoints

### Authentication

**POST /api/auth/register**
- Request: `{"email": "user@example.com", "password": "password123"}`
- Response: `{"token": "jwt...", "user": {...}}`

**POST /api/auth/login**
- Request: `{"email": "user@example.com", "password": "password123"}`
- Response: `{"token": "jwt...", "user": {...}}`

### Plans (Protected — requires JWT)

**POST /api/plans/generate**
- Headers: `Authorization: Bearer <token>`
- Request: See scenarios above
- Response: `{"plan": {...}, "data_confidence": {...}}`

**GET /api/plans**
- Headers: `Authorization: Bearer <token>`
- Response: `{"plans": [...], "count": N}`

**GET /api/plans/<id>**
- Headers: `Authorization: Bearer <token>`
- Response: `{"plan": {...}}`

---

## Architecture

### Critical Design Rules

1. **LLM is NEVER used for business logic**
   - All eligibility, salary, timeline checks are deterministic (`app/data_loader.py`)
   - LLM only generates narrative summaries after checks pass
   - See DECISIONS.md for rationale

2. **All responses include data_confidence**
   - Tracks per-field data availability
   - Frontend displays "✓ Verified" (specific data), "~ Estimated" (generic fallback), or "○ Unavailable"

3. **Adding destination = adding JSON file**
   - Zero code changes required
   - File naming: `{destination}_{role}.json` (lowercase, underscores)

