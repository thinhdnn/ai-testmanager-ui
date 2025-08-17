#!/usr/bin/env python3
"""
Test script to verify inline fixture handling in template rendering
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.playwright_test_case import PlaywrightTestCaseGenerator

def test_inline_fixture_template():
    """Test template rendering with inline fixtures"""
    
    # Create generator instance
    generator = PlaywrightTestCaseGenerator()
    
    # Mock context with inline fixtures
    context = {
        'testCaseName': 'Test Inline Fixtures',
        'tags': ['@smoke', '@regression'],
        'steps': [
            {
                'action': 'Login As Admin',
                'playwrightCode': '',
                'expected': 'User logged in',
                'disabled': False,
                'data': None,
                'referenced_fixture_id': 'fixture-1',
                'referenced_fixture_type': 'extend',
                'referenced_fixture_name': 'loginAsAdmin'
            },
            {
                'action': 'Check User Status',
                'playwrightCode': '',
                'expected': 'Status verified',
                'disabled': False,
                'data': None,
                'referenced_fixture_id': 'fixture-2',
                'referenced_fixture_type': 'inline',
                'referenced_fixture_name': 'checkUserStatus'
            },
            {
                'action': 'Verify Permissions',
                'playwrightCode': 'await page.click(".permissions");',
                'expected': 'Permissions displayed',
                'disabled': False,
                'data': None,
                'referenced_fixture_id': 'fixture-3',
                'referenced_fixture_type': 'inline',
                'referenced_fixture_name': 'verifyPermissions'
            }
        ],
        'fixtures': [
            {
                'name': 'Login As Admin',
                'mode': 'extend',
                'exportName': 'loginAsAdmin',
                'type': 'extend'
            }
        ],
        'projectName': 'test-project'
    }
    
    # Load template
    template = generator._load_template()
    print("=== TEMPLATE CONTENT ===")
    print(template)
    print("\n=== CONTEXT ===")
    print(f"Steps: {len(context['steps'])}")
    for i, step in enumerate(context['steps']):
        print(f"  Step {i+1}: {step['action']} (fixture: {step.get('referenced_fixture_name')}, type: {step.get('referenced_fixture_type')})")
    
    # Render template
    rendered = generator._render_template(template, context)
    
    print("\n=== RENDERED RESULT ===")
    print(rendered)
    
    # Check if inline fixtures are called as functions
    if 'await checkUserStatus();' in rendered:
        print("\n✅ SUCCESS: Inline fixture 'checkUserStatus' is called as function")
    else:
        print("\n❌ FAILED: Inline fixture 'checkUserStatus' is not called as function")
    
    if 'await verifyPermissions();' in rendered:
        print("✅ SUCCESS: Inline fixture 'verifyPermissions' is called as function")
    else:
        print("❌ FAILED: Inline fixture 'verifyPermissions' is not called as function")
    
    # Check if extend fixture is in function signature
    if 'async ({ page, loginAsAdmin })' in rendered:
        print("✅ SUCCESS: Extend fixture 'loginAsAdmin' is in function signature")
    else:
        print("❌ FAILED: Extend fixture 'loginAsAdmin' is not in function signature")

if __name__ == "__main__":
    test_inline_fixture_template()
