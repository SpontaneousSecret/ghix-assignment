# Setup and Deployment Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari)
- (Optional) Gemini API key for AI narratives

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
cd /Users/sujalgupta/ghix-assgnment
pip install -r requirements.txt
```

This installs:
- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- SQLAlchemy==2.0.23
- PyJWT==2.8.0
- bcrypt==4.1.1
- python-dotenv==1.0.0
- requests==2.31.0

### 2. (Optional) Set Environment Variables

For production or to enable Gemini AI narratives:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
export JWT_SECRET_KEY="your-secret-jwt-key"
export SECRET_KEY="your-flask-secret-key"
```

Or create a `.env` file:

```
GEMINI_API_KEY=your-gemini-api-key-here
JWT_SECRET_KEY=your-secret-jwt-key
SECRET_KEY=your-flask-secret-key
```

### 3. Start the Backend Server

```bash
python3 run.py
```

Output should show:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**The backend is now running on port 5000**

### 4. Start the Frontend Server

Open a **new terminal window** and run:

```bash
cd /Users/sujalgupta/ghix-assgnment
python3 -m http.server 8080
```

Output should show:
```
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

**The frontend is now running on port 8080**

### 5. Access the Application

Open your web browser and navigate to:

```
http://localhost:8080/index.html
```

## Testing the Application

### Manual Testing (Web Interface)

1. **Register a new account**:
   - Click "Register" tab
   - Enter email and password
   - Click "Register" button

2. **Generate a relocation plan**:
   - Form is pre-filled with Scenario A defaults
   - Click "Generate Plan"
   - Review warnings, confidence badges, and AI narrative

3. **Test missing data error**:
   - Change destination to a non-existent one
   - Try to generate plan
   - Should see structured error with available destinations

4. **View saved plans**:
   - Click "View Saved Plans"
   - See all your generated plans
   - Click on a plan to view details

### Automated API Testing

Run the automated test suite:

```bash
python3 test_api.py
```

This tests:
- ✓ User registration
- ✓ User login
- ✓ Plan generation (success case)
- ✓ Plan generation (missing data error)
- ✓ List all plans
- ✓ Get plan by ID
- ✓ Unauthorized access blocking

### Manual API Testing with curl

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'

# 2. Login (save the token)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'

# 3. Generate plan (use token from login)
curl -X POST http://localhost:5000/api/plans/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "origin": "India",
    "destination": "Germany",
    "target_role": "Senior Backend Engineer",
    "salary_expectation": 45000,
    "currency": "EUR",
    "timeline_months": 12,
    "work_auth_constraint": "Need visa sponsorship"
  }'

# 4. List all plans
curl -X GET http://localhost:5000/api/plans \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 5. Get specific plan
curl -X GET http://localhost:5000/api/plans/1 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Database

### Location
```
instance/career_relocation.db
```

The database is created automatically on first run.

### Reset Database

To start fresh:

```bash
rm instance/career_relocation.db
python3 run.py  # Will create new database
```

### View Database Contents

```bash
sqlite3 instance/career_relocation.db

# Inside sqlite3:
.tables                    # List all tables
SELECT * FROM users;       # View users
SELECT * FROM relocation_plans;  # View plans
.quit                      # Exit
```

## Adding New Destinations

1. Create a JSON file in the `data/` directory
2. Name it: `{destination}_{role}.json` (lowercase, underscores)
3. Example: `data/canada_software_engineer.json`

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

**No code changes required!** The app automatically detects and loads new destination files.

## Troubleshooting

### Port Already in Use

If port 5000 or 8080 is already in use:

```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

### Database Locked

If you get "database is locked" error:

```bash
# Close all connections and restart
pkill -f "python3 run.py"
sleep 2
python3 run.py
```

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt --upgrade
```

### CORS Issues

The app currently runs backend and frontend on different ports. If you encounter CORS issues, you can:

1. Use a browser extension to disable CORS (development only)
2. Serve the frontend from Flask (add route in `app/__init__.py`)
3. Configure proper CORS headers in Flask

## Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Using uWSGI

```bash
pip install uwsgi

uwsgi --http :5000 --wsgi-file run.py --callable app
```

### Environment Variables for Production

```bash
export FLASK_ENV=production
export JWT_SECRET_KEY="strong-random-secret-key"
export SECRET_KEY="another-strong-secret-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

### Nginx Configuration (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/ghix-assgnment;
        index index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Performance Tips

1. **Database Indexing**: Already optimized with composite indexes
2. **Connection Pooling**: SQLAlchemy handles this automatically
3. **Caching**: Consider adding Redis for frequently accessed plans
4. **CDN**: Serve static assets (index.html) via CDN in production

## Security Checklist

- [x] Passwords hashed with bcrypt
- [x] JWT tokens with expiration
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] Input validation on all endpoints
- [ ] Rate limiting (TODO)
- [ ] HTTPS in production (TODO)
- [ ] CORS configuration (TODO)

## Support

For issues or questions:
1. Check this guide
2. Review README.md
3. Check API response error messages
4. Verify server logs in terminal

## Quick Reference

| Component | URL | Port |
|-----------|-----|------|
| Frontend | http://localhost:8080/index.html | 8080 |
| Backend API | http://localhost:5000 | 5000 |
| Database | instance/career_relocation.db | - |
| API Docs | (See README.md) | - |
