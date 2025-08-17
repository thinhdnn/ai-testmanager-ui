#!/usr/bin/env python3
"""
Test script for fixture detail endpoint
"""

import requests
import json

def test_fixture_detail_endpoint():
    """Test the new fixture detail endpoint"""
    
    # Test with a sample fixture ID (you'll need to replace this with a real one)
    fixture_id = "400c09af-eeb0-43cd-8bca-f87d22170b0f"  # From your example
    
    try:
        # Test the new detail endpoint
        detail_url = f"http://localhost:8000/api/v1/fixtures/{fixture_id}/detail"
        print(f"Testing fixture detail endpoint: {detail_url}")
        
        response = requests.get(detail_url)
        
        if response.status_code == 200:
            fixture_detail = response.json()
            print("✅ Fixture detail endpoint working!")
            print(f"Fixture: {fixture_detail['name']}")
            print(f"Total Test Cases Used: {fixture_detail['total_test_cases_used']}")
            print(f"Test Cases: {len(fixture_detail['test_cases'])}")
            
            if fixture_detail['test_cases']:
                print("Test Cases Details:")
                for tc in fixture_detail['test_cases']:
                    print(f"  - {tc['name']} (Status: {tc['status']})")
            
            return fixture_detail
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        return None

def test_regular_fixture_endpoint():
    """Test the regular fixture endpoint for comparison"""
    
    fixture_id = "400c09af-eeb0-43cd-8bca-f87d22170b0f"
    
    try:
        regular_url = f"http://localhost:8000/api/v1/fixtures/{fixture_id}"
        print(f"\nTesting regular fixture endpoint: {regular_url}")
        
        response = requests.get(regular_url)
        
        if response.status_code == 200:
            fixture = response.json()
            print("✅ Regular fixture endpoint working!")
            print(f"Fixture: {fixture['name']}")
            print(f"Has test_cases field: {'test_cases' in fixture}")
            return fixture
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error testing endpoint: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Fixture Detail Endpoint")
    print("=" * 50)
    
    # Test both endpoints
    detail_result = test_fixture_detail_endpoint()
    regular_result = test_regular_fixture_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    if detail_result:
        print("✅ Fixture Detail Endpoint: WORKING")
        print(f"   - Total Test Cases: {detail_result['total_test_cases_used']}")
        print(f"   - Test Cases Details: {len(detail_result['test_cases'])} items")
    else:
        print("❌ Fixture Detail Endpoint: FAILED")
    
    if regular_result:
        print("✅ Regular Fixture Endpoint: WORKING")
        print(f"   - Basic Info: {regular_result['name']}")
    else:
        print("❌ Regular Fixture Endpoint: FAILED")
    
    print("\n🎯 Next Steps:")
    print("1. Make sure the FastAPI server is running")
    print("2. Check if the fixture ID exists in your database")
    print("3. Test with a real fixture ID from your system")
