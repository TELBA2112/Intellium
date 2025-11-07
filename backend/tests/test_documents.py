"""
Tests for document endpoints.

This module tests:
- Document upload
- Document listing
- Document retrieval
- Document deletion
"""

import io
from typing import BinaryIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User


@pytest.fixture
def sample_file() -> BinaryIO:
    """
    Create a sample file for testing uploads.
    
    Returns:
        Binary file-like object
    """
    return io.BytesIO(b"Sample document content for testing")


class TestDocumentUpload:
    """Test cases for document upload endpoint."""
    
    def test_upload_document_success(
        self,
        client: TestClient,
        user_token: str,
        sample_file: BinaryIO
    ):
        """
        Test successful document upload.
        
        Given: Authenticated user and valid file
        When: POST request to /documents/upload
        Then: Document is created and returned with 201 status
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        files = {"file": ("test.txt", sample_file, "text/plain")}
        data = {
            "title": "Test Document",
            "description": "A test document"
        }
        
        response = client.post(
            "/documents/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Test Document"
        assert result["description"] == "A test document"
        assert result["status"] == "pending"
        assert "id" in result
        assert "filename" in result
    
    def test_upload_document_unauthenticated(
        self,
        client: TestClient,
        sample_file: BinaryIO
    ):
        """
        Test upload without authentication.
        
        Given: No authentication token
        When: POST request to /documents/upload
        Then: 401 unauthorized error is returned
        """
        files = {"file": ("test.txt", sample_file, "text/plain")}
        data = {"title": "Test Document"}
        
        response = client.post(
            "/documents/upload",
            files=files,
            data=data
        )
        
        assert response.status_code == 401
    
    def test_upload_document_missing_title(
        self,
        client: TestClient,
        user_token: str,
        sample_file: BinaryIO
    ):
        """
        Test upload without required title.
        
        Given: File but no title
        When: POST request to /documents/upload
        Then: 422 validation error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        files = {"file": ("test.txt", sample_file, "text/plain")}
        
        response = client.post(
            "/documents/upload",
            headers=headers,
            files=files
        )
        
        assert response.status_code == 422
    
    def test_upload_document_no_file(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test upload without file.
        
        Given: Title but no file
        When: POST request to /documents/upload
        Then: 422 validation error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        data = {"title": "Test Document"}
        
        response = client.post(
            "/documents/upload",
            headers=headers,
            data=data
        )
        
        assert response.status_code == 422


class TestDocumentList:
    """Test cases for document listing endpoint."""
    
    def test_list_documents_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test listing documents with pagination.
        
        Given: User has uploaded documents
        When: GET request to /documents
        Then: Paginated list of documents is returned
        """
        # Create test documents
        for i in range(3):
            doc = Document(
                user_id=test_user.id,
                title=f"Document {i}",
                filename=f"doc{i}.txt",
                file_path=f"/path/to/doc{i}.txt",
                file_size=1024,
                mime_type="text/plain",
                status="completed"
            )
            db.add(doc)
        db.commit()
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/documents", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) == 3
    
    def test_list_documents_pagination(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test document listing with pagination parameters.
        
        Given: Multiple documents exist
        When: GET request with page and size params
        Then: Correct page of documents is returned
        """
        # Create 10 test documents
        for i in range(10):
            doc = Document(
                user_id=test_user.id,
                title=f"Document {i}",
                filename=f"doc{i}.txt",
                file_path=f"/path/to/doc{i}.txt",
                file_size=1024,
                mime_type="text/plain",
                status="completed"
            )
            db.add(doc)
        db.commit()
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(
            "/documents?page=2&size=3",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 3
        assert len(data["items"]) == 3
    
    def test_list_documents_unauthenticated(self, client: TestClient):
        """
        Test listing documents without authentication.
        
        Given: No authentication token
        When: GET request to /documents
        Then: 401 unauthorized error is returned
        """
        response = client.get("/documents")
        
        assert response.status_code == 401


class TestDocumentDetail:
    """Test cases for document detail endpoint."""
    
    def test_get_document_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test retrieving single document.
        
        Given: Document exists and user is owner
        When: GET request to /documents/{id}
        Then: Document details are returned
        """
        # Create test document
        doc = Document(
            user_id=test_user.id,
            title="Test Document",
            filename="test.txt",
            file_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            status="completed",
            ocr_text="Sample OCR text"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get(f"/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc.id
        assert data["title"] == "Test Document"
        assert data["ocr_text"] == "Sample OCR text"
    
    def test_get_document_not_found(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test retrieving non-existent document.
        
        Given: Document ID doesn't exist
        When: GET request to /documents/{id}
        Then: 404 not found error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.get("/documents/99999", headers=headers)
        
        assert response.status_code == 404
    
    def test_get_document_unauthorized_user(
        self,
        client: TestClient,
        db: Session
    ):
        """
        Test retrieving document owned by another user.
        
        Given: Document exists but owned by different user
        When: GET request to /documents/{id}
        Then: 403 forbidden error is returned
        """
        from app.core.security import create_access_token, get_password_hash
        
        # Create different user
        other_user = User(
            email="other@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Other User",
            is_active=True,
            is_superuser=False,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        
        # Create document for other user
        doc = Document(
            user_id=other_user.id,
            title="Other's Document",
            filename="test.txt",
            file_path="/path/to/test.txt",
            file_size=1024,
            mime_type="text/plain",
            status="completed"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Try to access with current user token
        token = create_access_token(data={"sub": "test@example.com"})
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/documents/{doc.id}", headers=headers)
        
        # Should either return 403 or 404 (implementation dependent)
        assert response.status_code in [403, 404]


class TestDocumentDelete:
    """Test cases for document deletion endpoint."""
    
    def test_delete_document_success(
        self,
        client: TestClient,
        user_token: str,
        db: Session,
        test_user: User
    ):
        """
        Test successful document deletion.
        
        Given: Document exists and user is owner
        When: DELETE request to /documents/{id}
        Then: Document is deleted and 204 returned
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
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.delete(f"/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verify document is deleted
        deleted_doc = db.query(Document).filter(Document.id == doc.id).first()
        assert deleted_doc is None
    
    def test_delete_document_not_found(
        self,
        client: TestClient,
        user_token: str
    ):
        """
        Test deleting non-existent document.
        
        Given: Document ID doesn't exist
        When: DELETE request to /documents/{id}
        Then: 404 not found error is returned
        """
        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.delete("/documents/99999", headers=headers)
        
        assert response.status_code == 404
