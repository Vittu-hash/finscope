#!/usr/bin/env python3
"""
FinScope Backend API Testing Suite
Tests all API endpoints including auth, budgeting, tips, and support
"""

import requests
import sys
import json
from datetime import datetime

class FinScopeAPITester:
    def __init__(self, base_url="https://money-mentor-352.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"Status: {response.status_code}"
                except:
                    response_data = {}
                    details = f"Status: {response.status_code} (No JSON response)"
            else:
                try:
                    error_data = response.json()
                    details = f"Expected {expected_status}, got {response.status_code}. Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:100]}"
                response_data = {}

            self.log_test(name, success, details)
            return success, response_data

        except requests.exceptions.RequestException as e:
            details = f"Request failed: {str(e)}"
            self.log_test(name, False, details)
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("User Registration", "POST", "auth/register", 201, user_data)
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_login(self):
        """Test user login with existing credentials"""
        # Try to login with the registered user
        if not hasattr(self, '_test_email'):
            # Create a new user for login test
            timestamp = datetime.now().strftime('%H%M%S')
            self._test_email = f"logintest{timestamp}@example.com"
            self._test_password = "LoginTest123!"
            
            # Register first
            register_data = {
                "name": f"Login Test User {timestamp}",
                "email": self._test_email,
                "password": self._test_password
            }
            
            success, _ = self.run_test("Pre-Login Registration", "POST", "auth/register", 201, register_data)
            if not success:
                return False

        # Now test login
        login_data = {
            "email": self._test_email,
            "password": self._test_password
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_user_profile(self):
        """Test getting current user profile"""
        if not self.token:
            self.log_test("Get User Profile", False, "No auth token available")
            return False
            
        return self.run_test("Get User Profile", "GET", "auth/me", 200)[0]

    def test_protected_route_without_auth(self):
        """Test accessing protected route without authentication"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, _ = self.run_test("Protected Route (No Auth)", "GET", "auth/me", 401)
        
        # Restore token
        self.token = temp_token
        return success

    def test_budget_plan_creation(self):
        """Test budget plan creation"""
        if not self.token:
            self.log_test("Budget Plan Creation", False, "No auth token available")
            return False
            
        plan_data = {
            "salary": 50000.0,
            "age": 30,
            "riskLevel": "Medium",
            "expenses": {
                "groceries": 5000,
                "rent": 15000,
                "utilities": 2000,
                "travel": 3000,
                "entertainment": 2000,
                "shopping": 2000,
                "health": 1000,
                "education": 1000,
                "savings": 5000,
                "other": 1000
            }
        }
        
        success, response = self.run_test("Budget Plan Creation", "POST", "plan", 200, plan_data)
        
        if success:
            # Verify response structure
            required_fields = ['recommendedPlan', 'actualSummary', 'comparison', 'insights']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Budget Plan Response Structure", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Budget Plan Response Structure", True, "All required fields present")
                
        return success

    def test_tips_endpoint(self):
        """Test tips endpoint"""
        success, response = self.run_test("Get Financial Tips", "GET", "tips", 200)
        
        if success:
            # Verify response structure
            required_fields = ['dailyTip', 'microLessons']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Tips Response Structure", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Tips Response Structure", True, "All required fields present")
                
        return success

    def test_support_request(self):
        """Test support request submission"""
        support_data = {
            "name": "Test User",
            "email": "test@example.com",
            "message": "This is a test support request from automated testing."
        }
        
        success, response = self.run_test("Support Request", "POST", "support", 201, support_data)
        
        if success and 'id' in response:
            self.log_test("Support Request Response", True, f"Request ID: {response['id']}")
        
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints return 404"""
        return self.run_test("Invalid Endpoint", "GET", "nonexistent", 404)[0]

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting FinScope Backend API Tests")
        print("=" * 50)
        
        # Basic connectivity
        self.test_health_check()
        
        # Authentication tests
        self.test_register()
        self.test_login()
        self.test_get_user_profile()
        self.test_protected_route_without_auth()
        
        # Feature tests (require authentication)
        self.test_budget_plan_creation()
        self.test_tips_endpoint()
        self.test_support_request()
        
        # Error handling
        self.test_invalid_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

    def get_test_report(self):
        """Get detailed test report"""
        return {
            "summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "failed_tests": self.tests_run - self.tests_passed,
                "success_rate": f"{(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%"
            },
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = FinScopeAPITester()
    exit_code = tester.run_all_tests()
    
    # Save detailed report
    report = tester.get_test_report()
    with open('/app/backend_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: /app/backend_test_report.json")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())