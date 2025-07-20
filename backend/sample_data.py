#!/usr/bin/env python3
"""
Sample data script for AI Test Manager
Creates sample projects, test cases, and users for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.crud import user as crud_user, project as crud_project, test_case as crud_test_case, step as crud_step, project_setting as crud_setting, test_result as crud_result, release as crud_release
from app.schemas.user import UserCreate
from app.schemas.project import ProjectCreate
from app.schemas.test_case import TestCaseCreate
from app.schemas.step import StepCreate
from app.schemas.project_setting import ProjectSettingCreate
from app.schemas.test_result import TestResultHistoryCreate, TestCaseExecutionCreate
from app.schemas.release import ReleaseCreate, ReleaseTestCaseCreate
from datetime import datetime
from app.models.tag import Tag


def create_sample_data():
    db = SessionLocal()
    
    try:
        # Create sample users
        print("Creating sample users...")
        
        admin_user = UserCreate(
            username="admin",
            email="admin@testmanager.com",
            password="admin123"
        )
        
        test_user = UserCreate(
            username="tester1",
            email="tester1@testmanager.com", 
            password="test123"
        )
        
        # Check if users already exist
        existing_admin = crud_user.get_user_by_username(db, "admin")
        existing_tester = crud_user.get_user_by_username(db, "tester1")
        
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            db_admin = existing_admin
        else:
            db_admin = crud_user.create_user(db, admin_user)
            
        if existing_tester:
            print(f"Tester user already exists: {existing_tester.username}")
            db_tester = existing_tester
        else:
            db_tester = crud_user.create_user(db, test_user)
        
        print(f"Created users: {db_admin.username}, {db_tester.username}")
        
        # Create sample projects
        print("Creating sample projects...")
        
        ecommerce_project = ProjectCreate(
            name="E-commerce Website Tests",
            description="Automated tests for our e-commerce platform",
            environment="staging",
            playwright_project_path="/tests/ecommerce",
            created_by=str(db_admin.id)
        )
        
        mobile_project = ProjectCreate(
            name="Mobile App Tests", 
            description="Test suite for mobile application",
            environment="development",
            created_by=str(db_admin.id)
        )
        
        db_ecommerce = crud_project.create_project(db, ecommerce_project, created_by=str(db_admin.id))
        db_mobile = crud_project.create_project(db, mobile_project, created_by=str(db_admin.id))
        
        print(f"Created projects: {db_ecommerce.name}, {db_mobile.name}")
        
        # Create sample global tags
        print("Creating sample global tags...")
        global_tags = [
            Tag(value="smoke", label="Smoke Test"),
            Tag(value="regression", label="Regression"),
            Tag(value="auth", label="Authentication"),
            Tag(value="checkout", label="Checkout"),
            Tag(value="mobile", label="Mobile"),
        ]
        for tag in global_tags:
            db.add(tag)
        db.commit()
        print(f"Created {len(global_tags)} global tags.")
        
        # Create sample test cases
        print("Creating sample test cases...")
        
        test_cases = [
            TestCaseCreate(
                name="User Login Test",
                project_id=db_ecommerce.id,
                status="passed",
                order=1,
                playwright_script="test('user can login', async ({ page }) => { /* test code */ });",
                tags="auth,login",
                created_by=str(db_tester.id)
            ),
            TestCaseCreate(
                name="Add Product to Cart",
                project_id=db_ecommerce.id,
                status="pending",
                order=2,
                playwright_script="test('add product to cart', async ({ page }) => { /* test code */ });",
                tags="cart,product",
                created_by=str(db_tester.id)
            ),
            TestCaseCreate(
                name="Checkout Process",
                project_id=db_ecommerce.id,
                status="failed",
                order=3,
                playwright_script="test('checkout process', async ({ page }) => { /* test code */ });",
                tags="checkout,payment",
                created_by=str(db_tester.id)
            ),
            TestCaseCreate(
                name="App Launch Test",
                project_id=db_mobile.id,
                status="passed",
                order=1,
                is_manual=True,
                tags="mobile,launch",
                created_by=str(db_tester.id)
            ),
            TestCaseCreate(
                name="Navigation Test",
                project_id=db_mobile.id,
                status="pending",
                order=2,
                is_manual=True,
                tags="mobile,navigation",
                created_by=str(db_tester.id)
            )
        ]
        
        created_test_cases = []
        for test_case in test_cases:
            db_test_case = crud_test_case.create_test_case(db, test_case)
            created_test_cases.append(db_test_case)
            print(f"Created test case: {db_test_case.name}")
        
        # Create sample steps for test cases
        print("Creating sample steps...")
        
        # Steps for login test case
        login_steps = [
            StepCreate(
                test_case_id=str(created_test_cases[0].id),  # User Login Test
                action="navigate",
                data="https://shop.example.com/login",
                expected="Login page is displayed",
                order=1,
                created_by=str(db_tester.id)
            ),
            StepCreate(
                test_case_id=str(created_test_cases[0].id),
                action="type",
                data='{"selector": "#username", "value": "testuser@example.com"}',
                expected="Username is entered",
                order=2,
                created_by=str(db_tester.id)
            ),
            StepCreate(
                test_case_id=str(created_test_cases[0].id),
                action="type",
                data='{"selector": "#password", "value": "password123"}',
                expected="Password is entered",
                order=3,
                created_by=str(db_tester.id)
            ),
            StepCreate(
                test_case_id=str(created_test_cases[0].id),
                action="click",
                data='{"selector": "#login-button"}',
                expected="User is redirected to dashboard",
                order=4,
                created_by=str(db_tester.id)
            )
        ]
        
        # Steps for add to cart test case
        cart_steps = [
            StepCreate(
                test_case_id=str(created_test_cases[1].id),  # Add Product to Cart
                action="navigate",
                data="https://shop.example.com/products/123",
                expected="Product page is displayed",
                order=1,
                created_by=str(db_tester.id)
            ),
            StepCreate(
                test_case_id=str(created_test_cases[1].id),
                action="click",
                data='{"selector": ".add-to-cart-btn"}',
                expected="Product is added to cart",
                order=2,
                created_by=str(db_tester.id)
            ),
            StepCreate(
                test_case_id=str(created_test_cases[1].id),
                action="verify",
                data='{"selector": ".cart-count", "text": "1"}',
                expected="Cart count shows 1 item",
                order=3,
                created_by=str(db_tester.id)
            )
        ]
        
        # Create all steps
        all_steps = login_steps + cart_steps
        step_count = 0
        for step in all_steps:
            db_step = crud_step.create_step(db, step)
            step_count += 1
            print(f"Created step: {db_step.action} (order: {db_step.order})")
        
        # Create sample project settings
        print("Creating sample project settings...")
        
        # Settings for e-commerce project
        ecommerce_settings = [
            ProjectSettingCreate(
                project_id=str(db_ecommerce.id),
                key="playwright_timeout",
                value="30000",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_ecommerce.id),
                key="playwright_headless",
                value="true",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_ecommerce.id),
                key="base_url",
                value="https://shop.example.com",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_ecommerce.id),
                key="api_endpoint",
                value="https://api.shop.example.com/v1",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_ecommerce.id),
                key="slack_webhook",
                value="https://hooks.slack.com/services/xxx",
                created_by=str(db_admin.id)
            )
        ]
        
        # Settings for mobile project
        mobile_settings = [
            ProjectSettingCreate(
                project_id=str(db_mobile.id),
                key="app_package",
                value="com.example.mobileapp",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_mobile.id),
                key="device_name",
                value="iPhone 15 Pro",
                created_by=str(db_admin.id)
            ),
            ProjectSettingCreate(
                project_id=str(db_mobile.id),
                key="parallel_tests",
                value="false",
                created_by=str(db_admin.id)
            )
        ]
        
        # Create all settings
        all_settings = ecommerce_settings + mobile_settings
        setting_count = 0
        for setting in all_settings:
            db_setting = crud_setting.create_project_setting(db, setting)
            setting_count += 1
            print(f"Created setting: {db_setting.key} = {db_setting.value}")
        
        # Create sample releases
        print("Creating sample releases...")
        
        # Releases for ecommerce project
        ecommerce_releases = [
            ReleaseCreate(
                project_id=str(db_ecommerce.id),
                name="Sprint 1 Release",
                version="v1.0.0",
                description="First major release with core shopping features",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                status="released",
                created_by=str(db_admin.id)
            ),
            ReleaseCreate(
                project_id=str(db_ecommerce.id),
                name="Sprint 2 Release",
                version="v1.1.0",
                description="Enhanced checkout and payment features",
                start_date=datetime(2024, 2, 1),
                end_date=datetime(2024, 2, 28),
                status="testing",
                created_by=str(db_admin.id)
            )
        ]
        
        # Releases for mobile project
        mobile_releases = [
            ReleaseCreate(
                project_id=str(db_mobile.id),
                name="Beta Release",
                version="v0.9.0",
                description="Beta version for testing",
                start_date=datetime(2024, 1, 15),
                end_date=datetime(2024, 2, 15),
                status="in_progress",
                created_by=str(db_tester.id)
            )
        ]
        
        # Create releases
        all_releases = ecommerce_releases + mobile_releases
        created_releases = []
        for release in all_releases:
            db_release = crud_release.create_release(db, release)
            created_releases.append(db_release)
            print(f"Created release: {db_release.name} ({db_release.version})")
        
        # Create release test case mappings
        print("Creating release test case mappings...")
        
        release_mappings = [
            # Sprint 1 Release test cases
            ReleaseTestCaseCreate(
                release_id=str(created_releases[0].id),
                test_case_id=str(created_test_cases[0].id),  # User Login Test
                version="1.0.0",
                created_by=str(db_admin.id)
            ),
            ReleaseTestCaseCreate(
                release_id=str(created_releases[0].id),
                test_case_id=str(created_test_cases[1].id),  # Add Product to Cart
                version="1.0.0",
                created_by=str(db_admin.id)
            ),
            
            # Sprint 2 Release test cases
            ReleaseTestCaseCreate(
                release_id=str(created_releases[1].id),
                test_case_id=str(created_test_cases[1].id),  # Add Product to Cart
                version="1.1.0",
                created_by=str(db_admin.id)
            ),
            ReleaseTestCaseCreate(
                release_id=str(created_releases[1].id),
                test_case_id=str(created_test_cases[2].id),  # Checkout Process
                version="1.1.0",
                created_by=str(db_admin.id)
            ),
            
            # Beta Release test cases
            ReleaseTestCaseCreate(
                release_id=str(created_releases[2].id),
                test_case_id=str(created_test_cases[3].id),  # App Launch Test
                version="0.9.0",
                created_by=str(db_tester.id)
            ),
            ReleaseTestCaseCreate(
                release_id=str(created_releases[2].id),
                test_case_id=str(created_test_cases[4].id),  # Navigation Test
                version="0.9.0",
                created_by=str(db_tester.id)
            )
        ]
        
        release_mapping_count = 0
        for mapping in release_mappings:
            db_mapping = crud_release.add_test_case_to_release(db, mapping)
            release_mapping_count += 1
            print(f"Added test case to release: {db_mapping.version}")
        
        # Create sample test results
        print("Creating sample test results...")
        
        # Test result for e-commerce project
        ecommerce_result = TestResultHistoryCreate(
            project_id=str(db_ecommerce.id),
            name="Daily Regression Test",
            success=True,
            status="passed",
            execution_time=245000,  # in milliseconds
            output="All tests passed successfully",
            browser="chromium",
            created_by=str(db_admin.id),
            last_run_by=str(db_tester.id)
        )
        
        db_ecommerce_result = crud_result.create_test_result(db, ecommerce_result)
        print(f"Created test result: {db_ecommerce_result.name}")
        
        # Test result for mobile project
        mobile_result = TestResultHistoryCreate(
            project_id=str(db_mobile.id),
            name="Manual Test Session",
            success=False,
            status="failed",
            execution_time=180000,
            error_message="Navigation test failed on device",
            output="2 tests passed, 1 test failed",
            created_by=str(db_tester.id),
            last_run_by=str(db_tester.id)
        )
        
        db_mobile_result = crud_result.create_test_result(db, mobile_result)
        print(f"Created test result: {db_mobile_result.name}")
        
        # Create test case executions for e-commerce result
        executions = [
            TestCaseExecutionCreate(
                test_result_id=str(db_ecommerce_result.id),
                test_case_id=str(created_test_cases[0].id),  # Login test
                status="passed",
                duration=15000,
                output="Login test completed successfully"
            ),
            TestCaseExecutionCreate(
                test_result_id=str(db_ecommerce_result.id),
                test_case_id=str(created_test_cases[1].id),  # Add to cart test
                status="passed",
                duration=12000,
                output="Product added to cart successfully"
            ),
            TestCaseExecutionCreate(
                test_result_id=str(db_mobile_result.id),
                test_case_id=str(created_test_cases[3].id),  # App launch test
                status="passed",
                duration=8000,
                output="App launched successfully"
            ),
            TestCaseExecutionCreate(
                test_result_id=str(db_mobile_result.id),
                test_case_id=str(created_test_cases[4].id),  # Navigation test
                status="failed",
                duration=5000,
                error_message="Navigation button not found",
                output="Test failed at step 2"
            )
        ]
        
        execution_count = 0
        for execution in executions:
            db_execution = crud_result.create_test_case_execution(db, execution)
            execution_count += 1
            print(f"Created execution: {db_execution.status} for test case")
        
        print(f"\n✅ Sample data created successfully!")
        print(f"📊 Created: {len(test_cases)} test cases, {step_count} steps, {setting_count} settings, {len(created_releases)} releases, {release_mapping_count} release mappings, 2 test results, {execution_count} executions across 2 projects")
        print("🔗 You can now access the API at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data() 