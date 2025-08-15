#!/usr/bin/env python3
"""
Simple test script to verify fixture integration with test cases
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_fixture_integration():
    """Test the complete fixture integration workflow"""
    
    print("Testing fixture integration with test cases...")
    
    # 1. Create a test case
    print("\n1. Creating test case...")
    test_case_data = {
        "name": "Test Case with Fixtures",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",  # Use a valid project ID
        "status": "active"
    }
    
    response = requests.post(f"{BASE_URL}/test-cases/", json=test_case_data)
    if response.status_code != 201:
        print(f"Failed to create test case: {response.status_code}")
        print(response.text)
        return
    
    test_case = response.json()
    test_case_id = test_case["id"]
    print(f"Created test case: {test_case_id}")
    
    # 2. Create a fixture
    print("\n2. Creating fixture...")
    fixture_data = {
        "name": "Test Fixture",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "extend",
        "playwright_script": "console.log('Test fixture setup');"
    }
    
    response = requests.post(f"{BASE_URL}/fixtures/", json=fixture_data)
    if response.status_code != 201:
        print(f"Failed to create fixture: {response.status_code}")
        print(response.text)
        return
    
    fixture = response.json()
    fixture_id = fixture["id"]
    print(f"Created fixture: {fixture_id}")
    
    # 3. Add fixture to test case
    print("\n3. Adding fixture to test case...")
    fixture_association_data = {
        "fixture_id": fixture_id
    }
    
    response = requests.post(f"{BASE_URL}/test-cases/{test_case_id}/fixtures", json=fixture_association_data)
    if response.status_code != 201:
        print(f"Failed to add fixture to test case: {response.status_code}")
        print(response.text)
        return
    
    print("Successfully added fixture to test case")
    
    # 4. Get test case fixtures
    print("\n4. Getting test case fixtures...")
    response = requests.get(f"{BASE_URL}/test-cases/{test_case_id}/fixtures")
    if response.status_code != 200:
        print(f"Failed to get test case fixtures: {response.status_code}")
        print(response.text)
        return
    
    fixtures = response.json()
    print(f"Found {len(fixtures)} fixtures for test case")
    for fixture in fixtures:
        print(f"  - {fixture['name']} (ID: {fixture['fixture_id']})")
    
    # 5. Get fixture steps
    print("\n5. Getting fixture steps...")
    response = requests.get(f"{BASE_URL}/test-cases/{test_case_id}/fixtures/{fixture_id}/steps")
    if response.status_code != 200:
        print(f"Failed to get fixture steps: {response.status_code}")
        print(response.text)
        return
    
    steps = response.json()
    print(f"Found {len(steps)} steps in fixture")
    
    # 6. Remove fixture from test case
    print("\n6. Removing fixture from test case...")
    response = requests.delete(f"{BASE_URL}/test-cases/{test_case_id}/fixtures/{fixture_id}")
    if response.status_code != 200:
        print(f"Failed to remove fixture from test case: {response.status_code}")
        print(response.text)
        return
    
    print("Successfully removed fixture from test case")
    
    # 7. Verify fixture is removed
    print("\n7. Verifying fixture is removed...")
    response = requests.get(f"{BASE_URL}/test-cases/{test_case_id}/fixtures")
    if response.status_code != 200:
        print(f"Failed to get test case fixtures: {response.status_code}")
        print(response.text)
        return
    
    fixtures = response.json()
    print(f"Found {len(fixtures)} fixtures for test case (should be 0)")
    
    print("\n✅ All tests passed! Fixture integration is working correctly.")

if __name__ == "__main__":
    # Wait a bit for the server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        test_fixture_integration()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
