#!/usr/bin/env python3
"""
Automated API testing script for Career Relocation Planner.
Tests all endpoints and validates responses.
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = 'http://localhost:5000'
TEST_EMAIL = f'test_{datetime.now().timestamp()}@example.com'
TEST_PASSWORD = 'password123'

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}[TEST]{RESET} {name}")

def print_success(message):
    print(f"{GREEN}✓{RESET} {message}")

def print_error(message):
    print(f"{RED}✗{RESET} {message}")

def print_info(message):
    print(f"{YELLOW}ℹ{RESET} {message}")

def test_register():
    """Test user registration"""
    print_test("User Registration")

    response = requests.post(
        f'{API_BASE}/api/auth/register',
        json={
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        }
    )

    if response.status_code == 201:
        data = response.json()
        assert 'token' in data, "Token not in response"
        assert 'user' in data, "User not in response"
        print_success(f"User registered: {data['user']['email']}")
        return data['token']
    else:
        print_error(f"Registration failed: {response.json()}")
        return None

def test_login(email, password):
    """Test user login"""
    print_test("User Login")

    response = requests.post(
        f'{API_BASE}/api/auth/login',
        json={
            'email': email,
            'password': password
        }
    )

    if response.status_code == 200:
        data = response.json()
        assert 'token' in data, "Token not in response"
        print_success(f"Login successful: {data['user']['email']}")
        return data['token']
    else:
        print_error(f"Login failed: {response.json()}")
        return None

def test_generate_plan_success(token):
    """Test successful plan generation"""
    print_test("Generate Plan - Success (Germany)")

    response = requests.post(
        f'{API_BASE}/api/plans/generate',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'origin': 'India',
            'destination': 'Germany',
            'target_role': 'Senior Backend Engineer',
            'salary_expectation': 45000,
            'currency': 'EUR',
            'timeline_months': 12,
            'work_auth_constraint': 'Need visa sponsorship'
        }
    )

    if response.status_code == 201:
        data = response.json()
        assert 'plan' in data, "Plan not in response"
        assert 'data_confidence' in data, "Data confidence not in response"

        plan = data['plan']
        confidence = data['data_confidence']

        print_success(f"Plan generated: ID {plan['id']}")
        print_info(f"  Origin: {plan['origin']} → Destination: {plan['destination']}")
        print_info(f"  Role: {plan['target_role']}")
        print_info(f"  Confidence: {confidence['overall_confidence']}")

        # Check for warnings (salary shortfall expected)
        warnings = plan['plan'].get('warnings', [])
        if warnings:
            print_info(f"  Warnings: {len(warnings)}")
            for warning in warnings:
                print_info(f"    - {warning[:80]}...")

        return plan['id']
    else:
        print_error(f"Plan generation failed: {response.json()}")
        return None

def test_generate_plan_missing_data(token):
    """Test plan generation with missing destination data"""
    print_test("Generate Plan - Missing Data (Singapore)")

    response = requests.post(
        f'{API_BASE}/api/plans/generate',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'origin': 'India',
            'destination': 'Singapore',
            'target_role': 'Software Engineer',
            'salary_expectation': 80000,
            'currency': 'SGD',
            'timeline_months': 6,
            'work_auth_constraint': 'Need visa'
        }
    )

    if response.status_code == 404:
        data = response.json()
        assert data['error'] == 'missing_data', "Expected missing_data error"
        assert 'available_destinations' in data, "Available destinations not in response"

        print_success("Correctly returned missing data error")
        print_info(f"  Error: {data['message']}")
        print_info(f"  Available: {', '.join(data['available_destinations'])}")
        return True
    else:
        print_error(f"Expected 404, got {response.status_code}")
        return False

def test_list_plans(token):
    """Test listing all plans"""
    print_test("List All Plans")

    response = requests.get(
        f'{API_BASE}/api/plans',
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code == 200:
        data = response.json()
        assert 'plans' in data, "Plans not in response"
        assert 'count' in data, "Count not in response"

        print_success(f"Retrieved {data['count']} plan(s)")
        for plan in data['plans']:
            print_info(f"  Plan {plan['id']}: {plan['destination']} - {plan['target_role']}")
        return True
    else:
        print_error(f"List plans failed: {response.json()}")
        return False

def test_get_plan(token, plan_id):
    """Test getting a single plan"""
    print_test(f"Get Plan by ID ({plan_id})")

    response = requests.get(
        f'{API_BASE}/api/plans/{plan_id}',
        headers={'Authorization': f'Bearer {token}'}
    )

    if response.status_code == 200:
        data = response.json()
        assert 'plan' in data, "Plan not in response"

        plan = data['plan']
        print_success(f"Retrieved plan {plan['id']}")
        print_info(f"  {plan['origin']} → {plan['destination']}")
        print_info(f"  Generated: {plan['generated_at']}")

        # Verify plan structure
        assert 'plan' in plan, "Nested plan data not found"
        assert 'data_confidence' in plan, "Data confidence not found"

        plan_data = plan['plan']
        assert 'eligibility' in plan_data, "Eligibility not in plan"
        assert 'timeline' in plan_data, "Timeline not in plan"
        assert 'salary_analysis' in plan_data, "Salary analysis not in plan"
        assert 'narrative' in plan_data, "Narrative not in plan"

        print_success("Plan structure validated")
        return True
    else:
        print_error(f"Get plan failed: {response.json()}")
        return False

def test_unauthorized_access():
    """Test accessing protected endpoints without token"""
    print_test("Unauthorized Access")

    response = requests.get(f'{API_BASE}/api/plans')

    if response.status_code == 401:
        print_success("Correctly blocked unauthorized access")
        return True
    else:
        print_error(f"Expected 401, got {response.status_code}")
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Career Relocation Planner - API Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    results = []

    # Test 1: Register
    token = test_register()
    results.append(('Register', token is not None))

    if not token:
        print_error("\nRegistration failed. Cannot continue tests.")
        sys.exit(1)

    # Test 2: Login
    login_token = test_login(TEST_EMAIL, TEST_PASSWORD)
    results.append(('Login', login_token is not None))

    # Test 3: Generate plan - Success
    plan_id = test_generate_plan_success(token)
    results.append(('Generate Plan (Success)', plan_id is not None))

    # Test 4: Generate plan - Missing data
    missing_data_result = test_generate_plan_missing_data(token)
    results.append(('Generate Plan (Missing Data)', missing_data_result))

    # Test 5: List plans
    list_result = test_list_plans(token)
    results.append(('List Plans', list_result))

    # Test 6: Get plan by ID
    if plan_id:
        get_result = test_get_plan(token, plan_id)
        results.append(('Get Plan by ID', get_result))

    # Test 7: Unauthorized access
    unauth_result = test_unauthorized_access()
    results.append(('Unauthorized Access', unauth_result))

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {name}")

    print(f"\n{BLUE}Results:{RESET} {passed}/{total} tests passed")

    if passed == total:
        print(f"{GREEN}✓ All tests passed!{RESET}\n")
        sys.exit(0)
    else:
        print(f"{RED}✗ Some tests failed{RESET}\n")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)
