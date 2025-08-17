#!/usr/bin/env python3
"""
Test script for steps endpoint
"""

import requests
import json

def test_steps_endpoint():
    """Test the steps endpoint for a test case"""
    
    test_case_id = "58b05140-1b00-4d2f-91f7-537d3951d811"
    
    try:
        # Test the steps endpoint
        steps_url = f"http://localhost:8000/api/v1/test-cases/{test_case_id}/steps"
        print(f"Testing steps endpoint: {steps_url}")
        
        response = requests.get(steps_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            steps = response.json()
            print("✅ Steps endpoint working!")
            print(f"Number of steps: {len(steps)}")
            return steps
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        return None

def test_fixture_steps_endpoint():
    """Test the fixture steps endpoint"""
    
    fixture_id = "f1ce5069-2688-49c8-86a0-5104c938d3b7"
    
    try:
        # Test the fixture steps endpoint
        fixture_steps_url = f"http://localhost:8000/api/v1/fixtures/{fixture_id}/steps"
        print(f"\nTesting fixture steps endpoint: {fixture_steps_url}")
        
        response = requests.get(fixture_steps_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            steps = response.json()
            print("✅ Fixture steps endpoint working!")
            print(f"Number of steps: {len(steps)}")
            return steps
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Steps Endpoints")
    print("=" * 50)
    
    # Test both endpoints
    steps_result = test_steps_endpoint()
    fixture_steps_result = test_fixture_steps_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if steps_result is not None:
        print("✅ Test Case Steps Endpoint: WORKING")
        print(f"   - Steps Count: {len(steps_result)}")
    else:
        print("❌ Test Case Steps Endpoint: FAILED")
    
    if fixture_steps_result is not None:
        print("✅ Fixture Steps Endpoint: WORKING")
        print(f"   - Steps Count: {len(fixture_steps_result)}")
    else:
        print("❌ Fixture Steps Endpoint: FAILED")
    
    print("\n🔧 Next Steps:")
    print("1. Make sure the FastAPI server is running")
    print("2. Check if the server needs to be restarted after routing changes")
    print("3. Verify that the routes are properly registered")
    print("4. Check for any routing conflicts")
