from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from ..models.sprint import Release, ReleaseTestCase
from ..models.test_case import TestCase
from ..schemas.release import ReleaseCreate, ReleaseUpdate, ReleaseTestCaseCreate, ReleaseTestCaseUpdate


# ============ RELEASE CRUD ============

def get_release(db: Session, release_id: str) -> Optional[Release]:
    return db.query(Release).filter(Release.id == release_id).first()


def get_releases(db: Session, skip: int = 0, limit: int = 100) -> List[Release]:
    return db.query(Release).offset(skip).limit(limit).all()


def get_releases_by_project(db: Session, project_id: str) -> List[Release]:
    return db.query(Release).filter(
        Release.project_id == project_id
    ).order_by(Release.created_at.desc()).all()


def get_release_by_version(db: Session, project_id: str, version: str) -> Optional[Release]:
    return db.query(Release).filter(
        Release.project_id == project_id,
        Release.version == version
    ).first()


def create_release(db: Session, release: ReleaseCreate) -> Release:
    db_release = Release(
        project_id=release.project_id,
        name=release.name,
        version=release.version,
        description=release.description,
        start_date=release.start_date,
        end_date=release.end_date,
        status=release.status,
        created_by=release.created_by
    )
    db.add(db_release)
    db.commit()
    db.refresh(db_release)
    return db_release


def update_release(db: Session, release_id: str, release: ReleaseUpdate) -> Optional[Release]:
    db_release = get_release(db, release_id)
    if db_release:
        update_data = release.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_release, field, value)
        
        db.commit()
        db.refresh(db_release)
    return db_release


def delete_release(db: Session, release_id: str) -> bool:
    db_release = get_release(db, release_id)
    if db_release:
        db.delete(db_release)
        db.commit()
        return True
    return False


# ============ RELEASE TEST CASE CRUD ============

def get_release_test_case(db: Session, release_test_case_id: str) -> Optional[ReleaseTestCase]:
    return db.query(ReleaseTestCase).filter(ReleaseTestCase.id == release_test_case_id).first()


def get_release_test_cases(db: Session, release_id: str) -> List[ReleaseTestCase]:
    return db.query(ReleaseTestCase).filter(
        ReleaseTestCase.release_id == release_id
    ).all()


def get_release_test_cases_with_details(db: Session, release_id: str) -> List[dict]:
    """Get release test cases with test case details"""
    results = db.query(
        ReleaseTestCase,
        TestCase.name.label('test_case_name'),
        TestCase.status.label('test_case_status')
    ).join(
        TestCase, ReleaseTestCase.test_case_id == TestCase.id
    ).filter(
        ReleaseTestCase.release_id == release_id
    ).all()
    
    return [
        {
            **rtc.__dict__,
            'test_case_name': test_case_name,
            'test_case_status': test_case_status
        }
        for rtc, test_case_name, test_case_status in results
    ]


def add_test_case_to_release(db: Session, release_test_case: ReleaseTestCaseCreate) -> ReleaseTestCase:
    db_release_test_case = ReleaseTestCase(
        release_id=release_test_case.release_id,
        test_case_id=release_test_case.test_case_id,
        version=release_test_case.version,
        created_by=release_test_case.created_by
    )
    db.add(db_release_test_case)
    db.commit()
    db.refresh(db_release_test_case)
    return db_release_test_case


def update_release_test_case(db: Session, release_test_case_id: str, release_test_case: ReleaseTestCaseUpdate) -> Optional[ReleaseTestCase]:
    db_release_test_case = get_release_test_case(db, release_test_case_id)
    if db_release_test_case:
        update_data = release_test_case.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_release_test_case, field, value)
        
        db.commit()
        db.refresh(db_release_test_case)
    return db_release_test_case


def remove_test_case_from_release(db: Session, release_id: str, test_case_id: str) -> bool:
    db_release_test_case = db.query(ReleaseTestCase).filter(
        ReleaseTestCase.release_id == release_id,
        ReleaseTestCase.test_case_id == test_case_id
    ).first()
    
    if db_release_test_case:
        db.delete(db_release_test_case)
        db.commit()
        return True
    return False


def bulk_add_test_cases_to_release(db: Session, release_id: str, test_case_ids: List[str], version: str = "1.0.0", created_by: str = None) -> List[ReleaseTestCase]:
    """Add multiple test cases to a release"""
    results = []
    
    for test_case_id in test_case_ids:
        # Check if already exists
        existing = db.query(ReleaseTestCase).filter(
            ReleaseTestCase.release_id == release_id,
            ReleaseTestCase.test_case_id == test_case_id
        ).first()
        
        if not existing:
            release_test_case = ReleaseTestCase(
                release_id=release_id,
                test_case_id=test_case_id,
                version=version,
                created_by=created_by
            )
            db.add(release_test_case)
            results.append(release_test_case)
    
    db.commit()
    for result in results:
        db.refresh(result)
    
    return results


# ============ RELEASE ANALYTICS ============

def get_release_stats(db: Session, release_id: str) -> dict:
    """Get release statistics"""
    # Get all test cases in release with their current status
    test_cases_data = db.query(
        ReleaseTestCase,
        TestCase.status
    ).join(
        TestCase, ReleaseTestCase.test_case_id == TestCase.id
    ).filter(
        ReleaseTestCase.release_id == release_id
    ).all()
    
    total_test_cases = len(test_cases_data)
    
    if total_test_cases == 0:
        return {
            "total_test_cases": 0,
            "test_cases_by_status": {},
            "release_progress": 0.0
        }
    
    # Group by status
    status_counts = {}
    for _, status in test_cases_data:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate progress (passed tests / total tests)
    passed_tests = status_counts.get("passed", 0)
    release_progress = (passed_tests / total_test_cases) * 100
    
    return {
        "total_test_cases": total_test_cases,
        "test_cases_by_status": status_counts,
        "release_progress": round(release_progress, 2)
    }


def get_project_releases_summary(db: Session, project_id: str) -> List[dict]:
    """Get summary of all releases for a project"""
    releases = get_releases_by_project(db, project_id)
    
    summary = []
    for release in releases:
        stats = get_release_stats(db, str(release.id))
        summary.append({
            **release.__dict__,
            "stats": stats
        })
    
    return summary 