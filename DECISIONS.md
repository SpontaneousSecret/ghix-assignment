# Technical Decisions

## 1. Scope

### What Was Built
- Complete backend API (Flask + SQLAlchemy + SQLite)
  - User authentication with JWT (24h expiry) and bcrypt password hashing
  - Three plan endpoints: generate, list, get by ID
  - Deterministic validation layer (data_loader.py)
  - LLM integration with Gemini Flash for narrative generation
- Database layer with full history tracking
  - User model with secure authentication
  - RelocationPlan model storing complete plan history (no updates, only inserts)
  - 17 CRUD operations with error handling
- Single-page frontend (vanilla JavaScript)
  - Four views: Auth, Generate Form, Result, Saved Plans
  - JWT state management with localStorage
  - Data confidence badges and warning cards
- Two destination/role combinations
  - Germany: Senior Backend Engineer
  - UK: Product Manager

### What Was Skipped (and Why)

**Email Verification**
- Skipped: No email sending infrastructure
- Reason: MVP focused on core relocation logic; email verification adds operational complexity (SMTP setup, email templates, verification tokens) without demonstrating the unique value proposition
- Future: Would implement with SendGrid/AWS SES when user acquisition is validated

**Rate Limiting**
- Skipped: No rate limiting middleware
- Reason: Development/demo environment assumption; adds infrastructure (Redis) and complexity for minimal current user base
- Future: Would add Flask-Limiter with Redis backend when API becomes public-facing

**PostgreSQL**
- Skipped: Used SQLite instead
- Reason: Zero-configuration deployment for demo; avoids database server setup
- Trade-off: Write concurrency limitations (see "Scale Assumption" below)
- Future: Migrate to Postgres when concurrent user load exceeds ~10-20 simultaneous plan generations

**Streaming LLM Responses**
- Skipped: Single-shot API calls to Gemini Flash
- Reason: REST API simplicity; streaming adds complexity (WebSockets or SSE) and state management
- Trade-off: User waits 2-5 seconds for complete response vs. seeing progressive updates
- Future: Would implement Server-Sent Events (SSE) if narrative length increases significantly

---

## 2. AI vs Deterministic Logic

### Critical Separation of Concerns

**ALL business logic is deterministic** — the LLM is **only** a narrator, never a decision-maker.

### What's Deterministic (app/data_loader.py)

1. **Eligibility Checks**
   - `check_missing_data()`: Verifies destination data exists
   - Returns structured error immediately if no JSON file found
   - **NO LLM call** when data is missing

2. **Salary Mathematics**
   - `check_salary_shortfall()`: Compares user expectation vs. visa threshold
   - Exact calculation: `gap = threshold - user_salary`
   - Returns precise gap amount (e.g., "EUR 552.00 below threshold")
   - **NO LLM involvement** in numerical comparison

3. **Timeline Validation**
   - `check_timeline_conflict()`: Compares user timeline vs. minimum required
   - Simple arithmetic: `gap = route_min_months - user_months`
   - Returns warning with specific month shortage
   - **NO LLM involvement** in date math

### What the LLM Does (app/llm.py)

The LLM **only** receives pre-computed fields and generates a narrative summary:

```python
def generate_narrative(
    origin, destination, target_role,
    salary_expectation, currency, timeline_months,
    work_auth_constraint,
    destination_data,  # ← Already loaded from JSON
    warnings           # ← Already computed by deterministic checks
):
    # LLM receives FACTS, returns STORY
```

**LLM Input**: Verified facts (visa type, salary threshold, market data, warnings list)
**LLM Output**: 3-4 paragraph narrative explaining the plan in natural language

### Why This Separation Matters

**Deterministic logic ensures correctness:**
- Salary shortfall: Wrong answer = user applies for visa they can't get
- Timeline conflict: Wrong answer = user quits job with unrealistic timeline
- Eligibility: Wrong answer = user relocates to destination with no job market data

**LLM provides value:**
- Transforms structured data into human-readable guidance
- Addresses warnings with context
- Encourages users with realistic optimism

**Failure modes are isolated:**
- LLM API down? → Fallback to template-based narrative (app continues working)
- LLM hallucinates? → Doesn't matter, user sees deterministic warnings separately

---

## 3. Data Confidence Flow

Data confidence tracks **per-field reliability** from source through to frontend display.

### Source: JSON Files (data/)

Each destination file contains structured market data:
```json
{
  "visa_requirements": { ... },  // ← visa_data_available = true
  "timeline": { ... },           // ← timeline_data_available = true
  "salary_data": { ... }         // ← salary_data_available = true
}
```

If a field is missing or file doesn't exist:
- Field flag = `false`
- Overall confidence downgrades to "low" or "none"

### Backend: API Response (app/plans.py)

```python
data_confidence = {
    'salary_data_available': 'salary_data' in destination_data,
    'timeline_data_available': 'timeline' in destination_data,
    'visa_data_available': 'visa_requirements' in destination_data,
    'overall_confidence': 'high' if not warnings else 'medium'
}
```

**Every API response includes `data_confidence` field** (per CLAUDE.md requirement).

### Frontend: Visual Badges (index.html)

```javascript
const confidenceBadge = (available) => {
    if (available) {
        return '<span class="badge-verified">✓ Verified</span>';  // Green
    } else {
        return '<span class="badge-placeholder">○ Unavailable</span>';  // Gray
    }
};
```

**User sees confidence next to each section:**
- Eligibility section: Shows visa_data_available badge
- Timeline section: Shows timeline_data_available badge
- Salary section: Shows salary_data_available badge

### Why This Matters

Users can **make informed decisions** knowing which parts of their plan are data-backed vs. estimated:
- Green badge = "This threshold is from official visa requirements"
- Gray badge = "We don't have salary data for this role; use as rough guidance"

---

## 4. LLM Choice: Gemini Flash Free Tier

### Why Gemini Flash

1. **Zero Cost**
   - Free tier: 15 requests/minute, 1 million tokens/day
   - MVP budget: $0 vs. GPT-4 ($0.03/1K tokens)
   - Enables free demo deployment

2. **Speed**
   - Flash model: ~2-3 second responses
   - Acceptable UX for narrative generation
   - Faster than GPT-3.5-turbo for this use case

3. **REST API Simplicity**
   - Direct HTTP POST, no SDK required
   - Easy to swap providers (prompt engineering is provider-agnostic)
   - Minimal dependencies (just `requests`)

### Limitations Accepted

1. **Rate Limits**
   - 15 RPM = max 15 concurrent plan generations/minute
   - Mitigation: Fallback narrative if quota exceeded
   - Scale fix: Upgrade to paid tier or implement request queuing

2. **No Streaming**
   - User waits for complete response (2-5 seconds)
   - No progressive text display
   - Acceptable for short narratives (500 tokens max)

3. **Single Attempt, No Retry**
   - On API error → immediate fallback to template
   - No exponential backoff or retry logic
   - Reason: Narrative is nice-to-have, not critical path
   - Deterministic data (warnings, thresholds) is already in response

4. **No Fine-Tuning**
   - Generic Gemini model, not tuned for relocation advice
   - Prompt engineering handles domain knowledge
   - Acceptable for MVP; fine-tuning ROI unclear

### Fallback Strategy

```python
if not api_key or llm_api_fails:
    return _generate_fallback_narrative(...)
```

Template-based narrative uses same input data as LLM:
- Consistent structure regardless of LLM availability
- **All deterministic warnings still appear**
- Slightly less natural language, but factually identical

---

## 5. Scale Assumption That Breaks: SQLite Write Locks

### Current Architecture (Works for <10 concurrent users)

```
User Request → Flask → SQLAlchemy → SQLite → Single write lock
```

**SQLite limitation**: Only **one writer at a time**

### What Breaks Under Concurrent Load

**Scenario**: 50 users generate plans simultaneously
1. Request 1 starts plan generation → acquires write lock
2. Request 2-50 arrive → **blocked waiting for lock**
3. Lock timeout (~5 seconds) → users see "database is locked" errors
4. Poor UX: requests serialize instead of parallelizing

**Root cause**: SQLite is file-based, not a concurrent database server

### Migration Path to Scale

**Replace SQLite → PostgreSQL + async task queue**

```
User Request → Flask → Celery → Redis (queue) → Worker → Postgres
                ↓
        Return plan_id + status=pending
```

**Changes needed:**

1. **PostgreSQL + Connection Pooling**
   ```python
   SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@host/db'
   SQLALCHEMY_POOL_SIZE = 20
   SQLALCHEMY_MAX_OVERFLOW = 40
   ```
   - Concurrent reads/writes with MVCC (Multi-Version Concurrency Control)
   - No write locks between transactions

2. **Celery Task Queue**
   ```python
   @celery.task
   def generate_plan_async(user_id, plan_params):
       # Call LLM (can take 2-5 seconds)
       # Write to Postgres
       return plan_id
   ```
   - Offload LLM API call to background worker
   - API returns immediately with `plan_id` and `status=pending`

3. **Status Polling or WebSocket**
   ```python
   GET /api/plans/<id>
   # Returns: { "status": "pending" | "completed" | "failed" }
   ```
   - Frontend polls every 2 seconds until `status=completed`
   - Or: WebSocket push notification when plan ready

**Infrastructure**:
- Redis for Celery message broker
- Postgres RDS (AWS) or Cloud SQL (GCP)
- 2-5 Celery worker processes

**Estimated capacity**: 500+ concurrent users with this setup

---

## 6. Hindsight: One Thing I'd Do Differently

### What I'd Change: Separate the Data Validation Layer into a Shared Module

**Current structure:**
```
app/data_loader.py  ← Validation functions
app/plans.py        ← Endpoint logic + validation orchestration
```

**Problem**: `app/plans.py` has 200+ lines mixing:
- HTTP request handling (Flask routes)
- Validation orchestration (calling data_loader functions)
- Response formatting (building data_confidence dict)
- Database operations (calling create_relocation_plan)

**Better structure:**
```
app/
├── services/
│   ├── plan_validator.py      ← All validation orchestration
│   └── plan_generator.py      ← LLM + database logic
├── api/
│   └── plans.py               ← Thin Flask routes only
└── data_loader.py             ← Unchanged (atomic checks)
```

**Why this helps:**

1. **Testability**
   - Can unit test `PlanValidator.validate()` without Flask context
   - Mock LLM calls in `PlanGenerator` independently
   - Current code requires Flask app context for testing

2. **Reusability**
   - CLI tool could call `PlanGenerator` directly (no Flask)
   - Background job could validate plans without HTTP
   - Mobile app backend could import same service layer

3. **Clarity**
   - `plans.py` would be ~50 lines of pure HTTP handling
   - Business logic lives in services with clear interfaces
   - Easier for new developers to understand boundaries

**What held me back:**
- MVP time pressure: "Make it work first, structure later"
- Flask tutorial patterns: routes + database in same file
- Didn't foresee testing complexity until after implementation

**Lesson learned:**
Even in MVPs, **separate domain logic from framework code early**.
The refactor cost is low upfront, high later (especially after tests are written around the coupled structure).

---

## Summary

These decisions optimized for:
- ✅ **Correctness first**: Deterministic logic protects users from wrong visa/salary advice
- ✅ **Fast MVP delivery**: SQLite, no email, no rate limiting, free LLM
- ✅ **Clear upgrade path**: Postgres + Celery when scale demands it
- ✅ **Honest trade-offs**: Every "skipped" feature has a documented reason

**Key insight**: The LLM is a UI enhancement, not the brain of the system. The brain is `data_loader.py` + structured JSON files.
