import requests
import sys
import json
from datetime import datetime

class APIKeyFunctionalityTester:
    def __init__(self, base_url="https://14850a6e-97b5-49a1-a2ae-3f96d13b55f6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_ids = []

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
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_session_creation_with_api_keys(self):
        """Test session creation with API keys"""
        print("\n=== Testing Session Creation with API Keys ===")
        
        # Test 1: Session with API keys provided
        session_data_with_keys = {
            "host_llm": {
                "provider": "anthropic",
                "model_name": "claude-sonnet-4-20250514",
                "display_name": "Claude Sonnet 4"
            },
            "target_llm": {
                "provider": "gemini", 
                "model_name": "gemini-2.0-flash",
                "display_name": "Gemini 2.0 Flash"
            },
            "protocol": "mcp",
            "api_keys": {
                "openai": "sk-test-openai-key",
                "anthropic": "sk-ant-test-key",
                "gemini": "AI-test-gemini-key"
            }
        }
        
        success, response = self.run_test(
            "Session Creation with API Keys", 
            "POST", 
            "session", 
            200, 
            session_data_with_keys
        )
        
        if success:
            session_id = response.get('id')
            self.session_ids.append(session_id)
            print(f"   ✓ Session created: {session_id}")
            
            # Verify API keys are NOT returned in response (security check)
            if 'api_keys' not in response:
                print("   ✅ Security Check: API keys not exposed in response")
                self.tests_passed += 1
            else:
                print("   ❌ Security Issue: API keys exposed in response")
            self.tests_run += 1
        
        return success

    def test_cross_provider_session(self):
        """Test cross-provider communication setup"""
        print("\n=== Testing Cross-Provider Communication ===")
        
        # Test different provider combinations
        test_cases = [
            {
                "name": "Anthropic → Gemini",
                "host": {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
                "target": {"provider": "gemini", "model_name": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash"}
            },
            {
                "name": "OpenAI → Anthropic", 
                "host": {"provider": "openai", "model_name": "gpt-4o", "display_name": "GPT-4o"},
                "target": {"provider": "anthropic", "model_name": "claude-3-5-sonnet-20241022", "display_name": "Claude 3.5 Sonnet"}
            },
            {
                "name": "Gemini → OpenAI",
                "host": {"provider": "gemini", "model_name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro"},
                "target": {"provider": "openai", "model_name": "gpt-4o-mini", "display_name": "GPT-4o Mini"}
            }
        ]
        
        all_success = True
        for case in test_cases:
            session_data = {
                "host_llm": case["host"],
                "target_llm": case["target"],
                "protocol": "natural",
                "api_keys": {
                    "openai": "sk-test-key",
                    "anthropic": "sk-ant-test-key", 
                    "gemini": "AI-test-key"
                }
            }
            
            success, response = self.run_test(
                f"Cross-Provider: {case['name']}", 
                "POST", 
                "session", 
                200, 
                session_data
            )
            
            if success:
                session_id = response.get('id')
                self.session_ids.append(session_id)
                print(f"   ✓ {case['name']} session created: {session_id}")
            else:
                all_success = False
        
        return all_success

    def test_demo_mode_all_protocols(self):
        """Test demo mode with all 4 protocols"""
        print("\n=== Testing Demo Mode with All Protocols ===")
        
        if not self.session_ids:
            print("   ⚠ No sessions available, creating one for demo testing...")
            # Create a simple session for demo testing
            session_data = {
                "host_llm": {"provider": "openai", "model_name": "gpt-4o", "display_name": "GPT-4o"},
                "target_llm": {"provider": "openai", "model_name": "gpt-4o-mini", "display_name": "GPT-4o Mini"},
                "protocol": "mcp"
            }
            success, response = self.run_test("Demo Session Creation", "POST", "session", 200, session_data)
            if success:
                self.session_ids.append(response.get('id'))
        
        if not self.session_ids:
            print("   ❌ Cannot test demo mode without a session")
            return False
        
        session_id = self.session_ids[0]
        protocols = ["mcp", "gibberlink", "droidspeak", "natural"]
        demo_queries = ["demo", "test", "demo capabilities", "test functionality"]
        
        all_success = True
        for protocol in protocols:
            for query in demo_queries[:2]:  # Test 2 queries per protocol
                extraction_data = {
                    "session_id": session_id,
                    "query": query,
                    "protocol": protocol
                }
                
                success, response = self.run_test(
                    f"Demo Mode - {protocol.upper()} Protocol with '{query}'",
                    "POST",
                    "extract", 
                    200,
                    extraction_data
                )
                
                if success:
                    # Verify demo response structure
                    expected_keys = ["query", "target_response", "host_analysis", "protocol_used"]
                    missing_keys = [key for key in expected_keys if key not in response]
                    
                    if not missing_keys:
                        print(f"   ✅ Demo response complete for {protocol}")
                        print(f"   ✓ Protocol used: {response.get('protocol_used')}")
                        print(f"   ✓ Response length: {len(response.get('target_response', ''))}")
                    else:
                        print(f"   ⚠ Missing keys in demo response: {missing_keys}")
                        all_success = False
                else:
                    all_success = False
        
        return all_success

    def test_error_handling_missing_keys(self):
        """Test error handling for missing API keys"""
        print("\n=== Testing Error Handling for Missing API Keys ===")
        
        # Test session creation without required API keys for non-OpenAI providers
        test_cases = [
            {
                "name": "Missing Anthropic Key",
                "host": {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
                "target": {"provider": "openai", "model_name": "gpt-4o", "display_name": "GPT-4o"},
                "api_keys": {"openai": "sk-test-key"}  # Missing anthropic key
            },
            {
                "name": "Missing Gemini Key",
                "host": {"provider": "openai", "model_name": "gpt-4o", "display_name": "GPT-4o"},
                "target": {"provider": "gemini", "model_name": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash"},
                "api_keys": {"openai": "sk-test-key"}  # Missing gemini key
            }
        ]
        
        all_success = True
        for case in test_cases:
            session_data = {
                "host_llm": case["host"],
                "target_llm": case["target"],
                "protocol": "mcp",
                "api_keys": case["api_keys"]
            }
            
            # Create session (should succeed)
            success, response = self.run_test(
                f"Session Creation - {case['name']}", 
                "POST", 
                "session", 
                200, 
                session_data
            )
            
            if success:
                session_id = response.get('id')
                print(f"   ✓ Session created: {session_id}")
                
                # Now test extraction (should fail with proper error)
                extraction_data = {
                    "session_id": session_id,
                    "query": "What are your capabilities?",
                    "protocol": "natural"
                }
                
                # This should fail with 400 status due to missing API key
                fail_success, error_response = self.run_test(
                    f"Extraction with {case['name']} (Expected Failure)",
                    "POST",
                    "extract",
                    400,  # Expecting failure
                    extraction_data
                )
                
                if fail_success:
                    print(f"   ✅ Proper error handling for {case['name']}")
                    print(f"   ✓ Error message: {error_response.get('detail', 'No detail')}")
                else:
                    print(f"   ⚠ Unexpected response for {case['name']}")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_api_key_security(self):
        """Test that API keys are handled securely"""
        print("\n=== Testing API Key Security ===")
        
        if not self.session_ids:
            print("   ⚠ No sessions available for security testing")
            return True
        
        session_id = self.session_ids[0]
        
        # Test 1: Get specific session - should not expose API keys
        success, response = self.run_test(
            "Session Retrieval Security Check",
            "GET",
            f"session/{session_id}",
            200
        )
        
        security_passed = True
        if success:
            if 'api_keys' in response:
                print("   ❌ Security Issue: API keys exposed in session retrieval")
                security_passed = False
            else:
                print("   ✅ Security Check: API keys not exposed in session retrieval")
        
        # Test 2: Get all sessions - should not expose API keys
        success, response = self.run_test(
            "Sessions List Security Check",
            "GET", 
            "sessions",
            200
        )
        
        if success and isinstance(response, list):
            for session in response:
                if 'api_keys' in session:
                    print("   ❌ Security Issue: API keys exposed in sessions list")
                    security_passed = False
                    break
            else:
                print("   ✅ Security Check: API keys not exposed in sessions list")
        
        if security_passed:
            self.tests_passed += 2
        self.tests_run += 2
        
        return security_passed

def main():
    print("🔐 Starting API Key Functionality Testing...")
    print("=" * 70)
    
    tester = APIKeyFunctionalityTester()
    
    # Run comprehensive API key tests
    tests = [
        ("Session Creation with API Keys", tester.test_session_creation_with_api_keys),
        ("Cross-Provider Communication", tester.test_cross_provider_session),
        ("Demo Mode All Protocols", tester.test_demo_mode_all_protocols),
        ("Error Handling Missing Keys", tester.test_error_handling_missing_keys),
        ("API Key Security", tester.test_api_key_security),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*70}")
    print(f"🔐 API KEY FUNCTIONALITY TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    print(f"Sessions Created: {len(tester.session_ids)}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API key functionality tests passed!")
        return 0
    else:
        print("⚠️  Some API key tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())