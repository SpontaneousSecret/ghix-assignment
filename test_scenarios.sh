#!/bin/bash

API="http://localhost:5000"

echo "Testing Scenario A and B..."
echo ""

# Scenario A: Germany
echo "=== SCENARIO A: India → Germany (Senior Backend Engineer) ==="
TOKEN_A=$(curl -s -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"eval_a@test.com","password":"password123"}' | jq -r '.token')

curl -s -X POST "$API/api/plans/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_A" \
  -d '{
    "origin": "India",
    "destination": "Germany",
    "target_role": "Senior Backend Engineer",
    "salary_expectation": 45000,
    "currency": "EUR",
    "timeline_months": 12,
    "work_auth_constraint": "Need visa sponsorship"
  }' | jq '{
    destination: .plan.destination,
    role: .plan.target_role,
    confidence: .data_confidence.overall_confidence,
    visa_type: .plan.plan.eligibility.visa_type,
    salary_threshold: .plan.plan.eligibility.min_salary_threshold,
    user_salary: .plan.salary_expectation,
    warnings_count: (.plan.plan.warnings | length),
    warnings: .plan.plan.warnings,
    action_steps: .plan.plan.timeline.breakdown,
    narrative_preview: (.plan.plan.narrative | .[0:150])
  }'

echo ""
echo ""

# Scenario B: UK
echo "=== SCENARIO B: India → UK (Product Manager) ==="
TOKEN_B=$(curl -s -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"eval_b@test.com","password":"password123"}' | jq -r '.token')

curl -s -X POST "$API/api/plans/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_B" \
  -d '{
    "origin": "India",
    "destination": "UK",
    "target_role": "Product Manager",
    "salary_expectation": 50000,
    "currency": "GBP",
    "timeline_months": 8,
    "work_auth_constraint": "Need visa sponsorship"
  }' | jq '{
    destination: .plan.destination,
    role: .plan.target_role,
    confidence: .data_confidence.overall_confidence,
    visa_type: .plan.plan.eligibility.visa_type,
    salary_threshold: .plan.plan.eligibility.min_salary_threshold,
    user_salary: .plan.salary_expectation,
    warnings_count: (.plan.plan.warnings | length),
    warnings: .plan.plan.warnings,
    action_steps: .plan.plan.timeline.breakdown,
    narrative_preview: (.plan.plan.narrative | .[0:150])
  }'

echo ""
echo ""
echo "=== KEY DIFFERENCES ==="
echo "Scenario A (Germany):"
echo "  - Visa: EU Blue Card"
echo "  - Threshold: EUR 45,552"
echo "  - User Salary: EUR 45,000"
echo "  - Warnings: 1 (salary shortfall EUR 552)"
echo "  - Confidence: medium"
echo ""
echo "Scenario B (UK):"
echo "  - Visa: Skilled Worker Visa"
echo "  - Threshold: GBP 38,700"
echo "  - User Salary: GBP 50,000"
echo "  - Warnings: 0 (salary exceeds threshold)"
echo "  - Confidence: high"
