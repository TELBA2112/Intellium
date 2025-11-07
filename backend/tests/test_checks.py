"""
Tests for similarity check endpoints.

This module tests:
- Quick similarity check
- Document check retrieval
- Check results listing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.check import QuickCheck, PatentMatch
from app.models.document import Document
from app.models.user import User


class TestQuickCheck:
    """Test cases for quick check endpoint."""
    
    def test_quick_check_success(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test successful quick similarity check.
        
        Given: Valid text to check
        When: POST request to /check/quick
        Then: Check results with matches are returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "text": "This is a sample patent description for testing similarity",
            "limit": 10,
            "threshold": 0.5,
            "mode": "fast"
        }
        
        response = client.post(
            "/check/quick",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "id" in result
        assert "total_matches" in result
        assert "avg_similarity" in result
        assert "max_similarity" in result
        assert "matches" in result
        assert isinstance(result["matches"], list)
    
    def test_quick_check_with_threshold(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test quick check with custom threshold.
        
        Given: Text with specific threshold
        When: POST request to /check/quick
        Then: Only matches above threshold are returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "text": "Patent description text",
            "limit": 5,
            "threshold": 0.8,  # High threshold
            "mode": "accurate"
        }
        
        response = client.post(
            "/check/quick",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # All matches should be above threshold
        for match in result["matches"]:
            assert match["similarity_score"] >= 0.8
    
    def test_quick_check_empty_text(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test quick check with empty text.
        
        Given: Empty text string
        When: POST request to /check/quick
        Then: 422 validation error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {
            "text": "",
            "limit": 10
        }
        
        response = client.post(
            "/check/quick",
            headers=headers,
            json=data
        )
        
        assert response.status_code == 422
    
    def test_quick_check_unauthenticated(self, client: TestClient):
        """
        Test quick check without authentication.
        
        Given: No authentication token
        When: POST request to /check/quick
        Then: 401 unauthorized error is returned
        """
        data = {
            "text": "Sample text",
            "limit": 10
        }
        
        response = client.post("/check/quick", json=data)
        
        assert response.status_code == 401


class TestDocumentChecks:
    """Test cases for document check retrieval."""
    
    def test_get_document_checks_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test retrieving checks for a document.
        
        Given: Document has associated checks
        When: GET request to /documents/{id}/checks
        Then: List of checks is returned
        """
        # Create test document
        doc = Document(
            user_id=test_user.id,
            title="Test Document",
            filename="test.txt",
            file_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            status="completed"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Create test check
        check = QuickCheck(
            document_id=doc.id,
            user_id=test_user.id,
            status="completed",
            total_matches=5,
            avg_similarity=0.65,
            max_similarity=0.89
        )
        db.add(check)
        db.commit()
        db.refresh(check)
        
        # Create test matches
        for i in range(5):
            match = PatentMatch(
                check_id=check.id,
                patent_number=f"US{1000000 + i}",
                patent_title=f"Patent Title {i}",
                similarity_score=0.5 + (i * 0.1),
                matched_text="Sample matched text"
            )
            db.add(match)
        db.commit()
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            f"/documents/{doc.id}/checks",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == check.id
        assert len(result[0]["matches"]) == 5
    
    def test_get_document_checks_no_checks(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test retrieving checks for document with no checks.
        
        Given: Document exists but has no checks
        When: GET request to /documents/{id}/checks
        Then: Empty list is returned
        """
        # Create test document without checks
        doc = Document(
            user_id=test_user.id,
            title="Test Document",
            filename="test.txt",
            file_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            f"/documents/{doc.id}/checks",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_document_checks_not_found(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test retrieving checks for non-existent document.
        
        Given: Document ID doesn't exist
        When: GET request to /documents/{id}/checks
        Then: 404 not found error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            "/documents/99999/checks",
            headers=headers
        )
        
        assert response.status_code == 404


class TestCheckResults:
    """Test cases for check result details."""
    
    def test_check_result_scoring(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test that check results calculate scores correctly.
        
        Given: Check with multiple matches
        When: Check is retrieved
        Then: avg_similarity and max_similarity are correct
        """
        # Create test document
        doc = Document(
            user_id=test_user.id,
            title="Test Document",
            filename="test.txt",
            file_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            status="completed"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Create check
        check = QuickCheck(
            document_id=doc.id,
            user_id=test_user.id,
            status="completed",
            total_matches=3,
            avg_similarity=0.70,
            max_similarity=0.90
        )
        db.add(check)
        db.commit()
        db.refresh(check)
        
        # Create matches with known scores
        scores = [0.60, 0.70, 0.90]
        for i, score in enumerate(scores):
            match = PatentMatch(
                check_id=check.id,
                patent_number=f"US{1000000 + i}",
                patent_title=f"Patent {i}",
                similarity_score=score,
                matched_text="Text"
            )
            db.add(match)
        db.commit()
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            f"/documents/{doc.id}/checks",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result[0]["max_similarity"] == 0.90
        assert result[0]["avg_similarity"] == 0.70
        assert result[0]["total_matches"] == 3
