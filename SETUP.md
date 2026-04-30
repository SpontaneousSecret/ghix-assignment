# Setup Guide

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- pip
- A modern web browser

---

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- flask-cors 4.0.0
- SQLAlchemy 2.0.36
- psycopg[binary] 3.2.4 (PostgreSQL driver)
- PyJWT 2.8.0
- bcrypt 4.1.1
- python-dotenv 1.0.0
- requests 2.31.0

### 2. Set Up PostgreSQL

```bash
# Create the database
createdb career_relocation

# (Optional) Create a dedicated user
createuser careerapp
psql -c "ALTER USER careerapp WITH PASSWORD 'yourpassword';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE career_relocation TO careerapp;"
```

### 3. Create a .env File

Create `.env` in the project root:

```
GROQ_API_KEY=gsk_your_key_here
DATABASE_URL=postgresql+psycopg://youruser@localhost:5432/career_relocation
JWT_SECRET_KEY=change-me-in-production
SECRET_KEY=change-me-in-production
```

**Important:** No spaces around `=` in `.env` files.

| Variable | Purpose | Required |
|----------|---------|----------|
| `GROQ_API_KEY` | Groq API key for AI narratives | No — falls back to template |
| `DATABASE_URL` | PostgreSQL connection string | No — defaults to local DB |
| `JWT_SECRET_KEY` | JWT signing secret | No — uses insecure dev default |
| `SECRET_KEY` | Flask session secret | No — uses insecure dev default |

### 4. Start the Backend

```bash
python3 run.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:8006
```

The backend runs on **port 8006**.

### 5. Open the Frontend

Open `index.html` directly in your browser, or serve it:

```bash
python3 -m http.server 8080
# Then open http://localhost:8080/index.html
```

The frontend API base URL is set to `http://localhost:8006`.

---

## Verified Destination/Role Combinations

Only these two have specific JSON data files with verified salary, visa, and timeline figures:

| Destination | Role |
|-------------|------|
| Germany | Senior Backend Engineer |
| UK | Product Manager |

Any other destination/role combination still works — the app uses global estimates and labels the data as "~ Estimated" instead of "✓ Verified".

---

## Adding New Destinations

1. Create a file in `data/` named `{destination}_{role}.json` (lowercase, underscores)
2. Follow this structure:

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

3. Restart the server — no code changes needed.

---

## Manual API Testing

```bash
# Register
curl -X POST http://localhost:8006/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'

# Login (copy the token)
curl -X POST http://localhost:8006/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'

# Generate plan
curl -X POST http://localhost:8006/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "origin": "India",
    "destination": "Germany",
    "target_role": "Senior Backend Engineer",
    "salary_expectation": 45000,
    "currency": "EUR",
    "timeline_months": 12,
    "work_auth_constraint": "Need visa sponsorship"
  }'

# List plans
curl http://localhost:8006/api/plans \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific plan
curl http://localhost:8006/api/plans/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Database

### View Contents

```bash
psql career_relocation

-- Inside psql:
\dt                             -- list tables
SELECT * FROM users;
SELECT id, destination, target_role, generated_at FROM relocation_plans;
\q
```

### Reset Database

```bash
dropdb career_relocation
createdb career_relocation
python3 run.py   # recreates tables on startup
```

---

## Troubleshooting

### Port Already in Use

```bash
lsof -ti:8006 | xargs kill -9
```

### PostgreSQL Connection Refused

```bash
# macOS (Homebrew)
brew services start postgresql@14

# Linux
sudo systemctl start postgresql
```

### .env Not Picked Up After Edit

The Werkzeug reloader only watches `.py` files. After editing `.env`, either restart the server manually or touch a Python file to trigger a reload:

```bash
touch app/llm.py
```

### Groq API Returning 429

The free tier has rate limits. The app automatically falls back to a template-based narrative — the plan still generates successfully with all deterministic data intact.

### Import Errors

```bash
pip install -r requirements.txt --upgrade
```

---

## Production Deployment

### Environment Variables

```bash
export FLASK_ENV=production
export JWT_SECRET_KEY="strong-random-secret-64-chars"
export SECRET_KEY="another-strong-secret"
export GROQ_API_KEY="gsk_..."
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/career_relocation"
```

### Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8006 "app:create_app()"
```

### Nginx (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/ghix-assgnment;
        index index.html;
    }

    location /api {
        proxy_pass http://localhost:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Security Checklist

- [x] Passwords hashed with bcrypt (12 rounds)
- [x] JWT tokens with 24h expiry
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Input validation on all endpoints
- [x] User ownership verification on plan access
- [ ] Rate limiting (add Flask-Limiter for public APIs)
- [ ] HTTPS (terminate at Nginx/load balancer)
- [ ] Rotate JWT_SECRET_KEY and SECRET_KEY from dev defaults

---

## Quick Reference

| Component | URL | Port |
|-----------|-----|------|
| Backend API | http://localhost:8006 | 8006 |
| Frontend (served) | http://localhost:8080/index.html | 8080 |
| Database | PostgreSQL `career_relocation` | 5432 |
