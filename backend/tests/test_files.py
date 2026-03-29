"""Tests for file upload endpoints"""
import pytest
from io import BytesIO
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestFileUpload:
    """Test single file upload"""

    def test_upload_text_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading a text file"""
        file_content = b"Hello, PAI!"
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            assert data["file"]["original_name"] == "test.txt"
            assert data["file"]["file_size"] == len(file_content)

    def test_upload_json_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading a JSON file"""
        file_content = b'{"key": "value"}'
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("data.json", BytesIO(file_content), "application/json")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    def test_upload_image_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading an image file"""
        # Minimal valid PNG header
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("image.png", BytesIO(png_header), "image/png")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    def test_upload_unsupported_file_type(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading unsupported file type"""
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("script.exe", BytesIO(b"malware"), "application/x-msdownload")},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_empty_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading empty file"""
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("empty.txt", BytesIO(b""), "text/plain")},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_file_too_large(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading file that's too large"""
        # Create file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("large.txt", BytesIO(large_content), "text/plain")},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_with_session_id(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading file with session ID"""
        file_content = b"Test content"
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id, "session_id": "session-123"},
            files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    def test_upload_without_user_id(self, test_client: TestClient, auth_headers: dict):
        """Test uploading without user_id"""
        response = test_client.post(
            "/api/v1/files/upload",
            files={"file": ("test.txt", BytesIO(b"content"), "text/plain")},
            headers=auth_headers
        )
        assert response.status_code == 422  # Missing required parameter


@pytest.mark.unit
class TestMultipleFileUpload:
    """Test multiple file uploads"""

    def test_upload_multiple_files(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading multiple files"""
        files = [
            ("file1.txt", BytesIO(b"Content 1"), "text/plain"),
            ("file2.txt", BytesIO(b"Content 2"), "text/plain"),
            ("file3.json", BytesIO(b'{"key": "value"}'), "application/json"),
        ]
        response = test_client.post(
            "/api/v1/files/upload-multiple",
            params={"user_id": valid_user_id},
            files=[("files", f) for f in files],
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            assert len(data["uploaded"]) == 3

    def test_upload_too_many_files(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading too many files at once"""
        # Create 6 files (exceeds max of 5)
        files = [
            (f"file{i}.txt", BytesIO(b"Content"), "text/plain")
            for i in range(6)
        ]
        response = test_client.post(
            "/api/v1/files/upload-multiple",
            params={"user_id": valid_user_id},
            files=[("files", f) for f in files],
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_multiple_mixed_validity(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading mix of valid and invalid files"""
        files = [
            ("valid.txt", BytesIO(b"Content"), "text/plain"),
            ("invalid.exe", BytesIO(b"malware"), "application/x-msdownload"),
            ("valid2.json", BytesIO(b'{"ok": true}'), "application/json"),
        ]
        response = test_client.post(
            "/api/v1/files/upload-multiple",
            params={"user_id": valid_user_id},
            files=[("files", f) for f in files],
            headers=auth_headers
        )
        # Should succeed with mixed results
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert len(data["uploaded"]) >= 2  # At least valid files uploaded
            assert len(data.get("errors", [])) >= 1  # At least one error


@pytest.mark.unit
class TestFileManagement:
    """Test file management endpoints"""

    def test_delete_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test deleting a file"""
        # First upload a file
        file_content = b"To delete"
        upload_response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("todelete.txt", BytesIO(file_content), "text/plain")},
            headers=auth_headers
        )

        if upload_response.status_code in [200, 201]:
            file_path = upload_response.json()["file"]["stored_path"]

            # Delete the file
            delete_response = test_client.delete(
                "/api/v1/files/delete",
                params={"file_path": file_path, "user_id": valid_user_id},
                headers=auth_headers
            )
            assert delete_response.status_code == 200

    def test_delete_nonexistent_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test deleting nonexistent file"""
        response = test_client.delete(
            "/api/v1/files/delete",
            params={"file_path": "/nonexistent/path/file.txt", "user_id": valid_user_id},
            headers=auth_headers
        )
        # Could be 404 or 403 depending on validation
        assert response.status_code in [403, 404]

    def test_cleanup_old_files(self, test_client: TestClient, auth_headers: dict):
        """Test cleaning up old files"""
        response = test_client.post(
            "/api/v1/files/cleanup",
            params={"days_old": 30},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data


@pytest.mark.unit
class TestFileValidation:
    """Test file validation"""

    def test_upload_markdown_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading markdown file"""
        md_content = b"# Header\n\nSome content"
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("readme.md", BytesIO(md_content), "text/markdown")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    def test_upload_pdf_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading PDF file"""
        pdf_header = b"%PDF-1.4\n" + b"x" * 100
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("document.pdf", BytesIO(pdf_header), "application/pdf")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    def test_upload_csv_file(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test uploading CSV file"""
        csv_content = b"name,age,city\nJohn,30,NYC\nJane,25,LA"
        response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("data.csv", BytesIO(csv_content), "text/csv")},
            headers=auth_headers
        )
        assert response.status_code in [200, 201]


@pytest.mark.integration
class TestFileWorkflow:
    """Integration tests for file workflows"""

    def test_upload_and_delete_workflow(self, test_client: TestClient, auth_headers: dict, valid_user_id: str):
        """Test complete upload and delete workflow"""
        # Upload
        file_content = b"Test workflow content"
        upload_response = test_client.post(
            "/api/v1/files/upload",
            params={"user_id": valid_user_id},
            files={"file": ("workflow.txt", BytesIO(file_content), "text/plain")},
            headers=auth_headers
        )
        assert upload_response.status_code in [200, 201]

        # Verify metadata
        file_data = upload_response.json()["file"]
        assert file_data["file_size"] == len(file_content)
        assert file_data["file_type"] == "txt"
        assert "file_hash" in file_data

        # Delete
        if upload_response.status_code in [200, 201]:
            file_path = file_data["stored_path"]
            delete_response = test_client.delete(
                "/api/v1/files/delete",
                params={"file_path": file_path, "user_id": valid_user_id},
                headers=auth_headers
            )
            assert delete_response.status_code == 200
