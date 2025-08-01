import requests
import sys
import json
from datetime import datetime

class NeuralBridgeAPITester:
    def __init__(self, base_url="https://14850a6e-97b5-49a1-a2ae-3f96d13b55f6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_get_models(self):
        """Test getting available models"""
        success, response = self.run_test("Get Available Models", "GET", "models", 200)
        if success and isinstance(response, dict):
            # Check if we have the expected model structure
            expected_providers = ["openai", "anthropic", "gemini"]
            for provider in expected_providers:
                if provider in response:
                    print(f"   ✓ Found {provider} models: {len(response[provider])} models")
                else:
                    print(f"   ⚠ Missing {provider} provider")
        return success

    def test_create_session(self):
        """Test creating a communication session"""
        session_data = {
            "host_llm": {
                "provider": "openai",
                "model_name": "gpt-4o",
                "display_name": "GPT-4o"
            },
            "target_llm": {
                "provider": "openai", 
                "model_name": "gpt-4o-mini",
                "display_name": "GPT-4o Mini"
            },
            "protocol": "mcp"
        }
        
        success, response = self.run_test("Create Communication Session", "POST", "session", 200, session_data)
        if success and isinstance(response, dict) and 'id' in response:
            self.session_id = response['id']
            print(f"   ✓ Session created with ID: {self.session_id}")
            print(f"   ✓ Host LLM: {response.get('host_llm', {}).get('display_name')}")
            print(f"   ✓ Target LLM: {response.get('target_llm', {}).get('display_name')}")
            print(f"   ✓ Protocol: {response.get('protocol')}")
        return success

    def test_get_sessions(self):
        """Test getting all sessions"""
        success, response = self.run_test("Get All Sessions", "GET", "sessions", 200)
        if success and isinstance(response, list):
            print(f"   ✓ Found {len(response)} sessions")
            if len(response) > 0:
                print(f"   ✓ Latest session: {response[-1].get('id', 'Unknown')}")
        return success

    def test_get_specific_session(self):
        """Test getting a specific session"""
        if not self.session_id:
            print("   ⚠ Skipping - No session ID available")
            return True
            
        success, response = self.run_test("Get Specific Session", "GET", f"session/{self.session_id}", 200)
        if success and isinstance(response, dict):
            print(f"   ✓ Retrieved session: {response.get('id')}")
        return success

    def test_extract_information(self):
        """Test information extraction"""
        if not self.session_id:
            print("   ⚠ Skipping - No session ID available")
            return True

        extraction_data = {
            "session_id": self.session_id,
            "query": "What are your core capabilities?",
            "protocol": "natural"
        }
        
        print("   🤖 Testing LLM communication - this may take 30+ seconds...")
        success, response = self.run_test("Extract Information", "POST", "extract", 200, extraction_data)
        
        if success and isinstance(response, dict):
            expected_keys = ["query", "target_response", "host_analysis", "protocol_used"]
            for key in expected_keys:
                if key in response:
                    print(f"   ✓ Found {key}: {str(response[key])[:50]}...")
                else:
                    print(f"   ⚠ Missing {key} in response")
        return success

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test creating status check
        status_data = {"client_name": "test_client"}
        success1, _ = self.run_test("Create Status Check", "POST", "status", 200, status_data)
        
        # Test getting status checks
        success2, response = self.run_test("Get Status Checks", "GET", "status", 200)
        if success2 and isinstance(response, list):
            print(f"   ✓ Found {len(response)} status checks")
        
        return success1 and success2

def main():
    print("🚀 Starting Neural Bridge API Testing...")
    print("=" * 60)
    
    tester = NeuralBridgeAPITester()
    
    # Run all tests
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Get Models", tester.test_get_models),
        ("Create Session", tester.test_create_session),
        ("Get Sessions", tester.test_get_sessions),
        ("Get Specific Session", tester.test_get_specific_session),
        ("Extract Information", tester.test_extract_information),
        ("Status Endpoints", tester.test_status_endpoints),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())