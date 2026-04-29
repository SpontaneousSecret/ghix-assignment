# Career Relocation App

## Stack
- Backend: Flask, SQLAlchemy, SQLite, PyJWT, bcrypt
- Frontend: Plain HTML + vanilla JS (single file per page)
- LLM: Gemini Flash free tier (via REST, not SDK)

## Project structure
app/__init__.py, app/models.py, app/auth.py, app/plans.py,
app/data_loader.py, app/llm.py
data/germany_senior_backend_engineer.json
data/uk_product_manager.json

## Critical rules
- NEVER use the LLM for eligibility checks, salary comparisons, or timeline logic
- LLM is only called AFTER deterministic checks pass, for narrative generation only
- All API responses must include a data_confidence field
- Adding a destination = adding a JSON file, zero code changes
- Endpoints must be mobile-API-friendly (not frontend-shaped responses)

## Auth
JWT tokens, 24h expiry, required on all /api/plans/* routes

## Edge cases (must work)
1. Timeline conflict → warning in response, not rejected
2. Salary shortfall → explicit message with exact gap amount
3. Missing data → structured error, no LLM call