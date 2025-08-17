#!/usr/bin/env python3
"""
Test script for fixture stats endpoint
"""

import requests
import json

def test_fixture_stats_endpoint():
    """Test the updated fixture stats endpoint"""
    
    # Test with the fixture ID from your example
    fixture_id = "f1ce5069-2688-49c8-86a0-5104c938d3b7"
    
    try:
        # Test the stats endpoint
        stats_url = f"http://localhost:8000/api/v1/test-results/fixtures/{fixture_id}/stats"
        print(f"Testing fixture stats endpoint: {stats_url}")
        
        response = requests.get(stats_url)
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Fixture stats endpoint working!")
            print(f"Total Executions: {stats['total_executions']}")
            print(f"Total Test Cases Used: {stats['total_test_cases_used']}")
            print(f"Success Rate: {stats['success_rate']}%")
            print(f"Average Duration: {stats['avg_duration']}ms")
            print(f"Last Status: {stats['last_status']}")
            
            return stats
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

def test_fixture_detail_endpoint():
    """Test the fixture detail endpoint for comparison"""
    
    fixture_id = "f1ce5069-2688-49c8-86a0-5104c938d3b7"
    
    try:
        detail_url = f"http://localhost:8000/api/v1/fixtures/{fixture_id}/detail"
        print(f"\nTesting fixture detail endpoint: {detail_url}")
        
        response = requests.get(detail_url)
        
        if response.status_code == 200:
            fixture_detail = response.json()
            print("✅ Fixture detail endpoint working!")
            print(f"Fixture: {fixture_detail['name']}")
            print(f"Total Test Cases Used: {fixture_detail['total_test_cases_used']}")
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

if __name__ == "__main__":
    print("🧪 Testing Updated Fixture Stats Endpoint")
    print("=" * 60)
    
    # Test both endpoints
    stats_result = test_fixture_stats_endpoint()
    detail_result = test_fixture_detail_endpoint()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if stats_result:
        print("✅ Fixture Stats Endpoint: WORKING")
        print(f"   - Total Executions: {stats_result['total_executions']}")
        print(f"   - Total Test Cases: {stats_result['total_test_cases_used']}")
        print(f"   - Success Rate: {stats_result['success_rate']}%")
        print(f"   - Last Status: {stats_result['last_status']}")
    else:
        print("❌ Fixture Stats Endpoint: FAILED")
    
    if detail_result:
        print("✅ Fixture Detail Endpoint: WORKING")
        print(f"   - Fixture Name: {detail_result['name']}")
        print(f"   - Total Test Cases: {detail_result['total_test_cases_used']}")
    else:
        print("❌ Fixture Detail Endpoint: FAILED")
    
    print("\n🎯 Expected Results:")
    print("- If fixture has test cases: total_test_cases_used > 0")
    print("- If fixture has executions: total_executions > 0")
    print("- Success rate should be calculated from actual executions")
    print("- Last status should reflect actual execution history")
    
    print("\n🔧 Next Steps:")
    print("1. Make sure the FastAPI server is running")
    print("2. Check if the fixture ID exists in your database")
    print("3. Verify that test cases are properly linked to fixtures")
    print("4. Check if there are test executions in the database")
