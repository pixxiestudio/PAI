"""File upload and management endpoints"""

import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.utils.file_handler import FileUploadHandler
from backend.db.models import Memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

# Initialize file upload handler
file_handler = FileUploadHandler(upload_dir="./uploads")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="User ID"),
    session_id: Optional[str] = Query(None, description="Session ID (optional)"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Upload a single file

    Args:
        file: File to upload
        user_id: User ID
        session_id: Optional session ID
        container: Service container
        db: Database session

    Returns:
        File metadata and storage information
    """
    try:
        # Read file content
        content = await file.read()

        # Validate file
        is_valid, error_msg = file_handler.validate_file(
            filename=file.filename,
            file_size=len(content),
            file_content=content
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Save file
        success, error, file_path = file_handler.save_file(
            filename=file.filename,
            file_content=content,
            user_id=user_id,
            session_id=session_id
        )

        if not success:
            raise HTTPException(status_code=500, detail=error)

        # Generate metadata
        metadata = file_handler.get_file_metadata(
            file_path=file_path,
            filename=file.filename,
            file_content=content
        )

        return {
            "success": True,
            "message": "File uploaded successfully",
            "file": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    user_id: str = Query(..., description="User ID"),
    session_id: Optional[str] = Query(None, description="Session ID (optional)"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Upload multiple files

    Args:
        files: Files to upload
        user_id: User ID
        session_id: Optional session ID
        container: Service container
        db: Database session

    Returns:
        List of file metadata for each uploaded file
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        if len(files) > FileUploadHandler.MAX_FILES_PER_REQUEST:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files (max {FileUploadHandler.MAX_FILES_PER_REQUEST})"
            )

        uploaded_files = []
        errors = []

        for idx, file in enumerate(files):
            try:
                content = await file.read()

                # Validate
                is_valid, error_msg = file_handler.validate_file(
                    filename=file.filename,
                    file_size=len(content),
                    file_content=content
                )

                if not is_valid:
                    errors.append({
                        "file": file.filename,
                        "error": error_msg
                    })
                    continue

                # Save
                success, error, file_path = file_handler.save_file(
                    filename=file.filename,
                    file_content=content,
                    user_id=user_id,
                    session_id=session_id
                )

                if not success:
                    errors.append({
                        "file": file.filename,
                        "error": error
                    })
                    continue

                # Generate metadata
                metadata = file_handler.get_file_metadata(
                    file_path=file_path,
                    filename=file.filename,
                    file_content=content
                )

                uploaded_files.append(metadata)

            except Exception as e:
                logger.error(f"Error uploading file {idx}: {str(e)}")
                errors.append({
                    "file": file.filename,
                    "error": str(e)
                })

        return {
            "success": len(uploaded_files) > 0,
            "message": f"Uploaded {len(uploaded_files)} files",
            "uploaded": uploaded_files,
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading multiple files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload files: {str(e)}"
        )


@router.delete("/delete")
async def delete_file(
    file_path: str = Query(..., description="Path to file to delete"),
    user_id: str = Query(..., description="User ID (for verification)"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Delete an uploaded file

    Args:
        file_path: Path to file
        user_id: User ID (must own the file)
        container: Service container
        db: Database session

    Returns:
        Success message
    """
    try:
        # Verify user owns the file (basic security check)
        if user_id not in file_path:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete files owned by other users"
            )

        success, error = file_handler.delete_file(file_path)

        if not success:
            raise HTTPException(status_code=404, detail=error)

        return {
            "success": True,
            "message": "File deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.post("/attach-to-memory")
async def attach_file_to_memory(
    memory_id: str = Query(..., description="Memory ID"),
    file_path: str = Query(..., description="File path"),
    user_id: str = Query(..., description="User ID"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Attach uploaded file to a memory

    Args:
        memory_id: Memory ID to attach to
        file_path: Path to uploaded file
        user_id: User ID
        container: Service container
        db: Database session

    Returns:
        Updated memory with file attachment
    """
    try:
        # Get memory
        memory = db.query(Memory).filter(Memory.id == memory_id).first()

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        if memory.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify memories owned by other users"
            )

        # Add file to memory metadata (if not already present)
        if not memory.additional_metadata:
            memory.additional_metadata = {}

        if "attachments" not in memory.additional_metadata:
            memory.additional_metadata["attachments"] = []

        # Add file attachment
        memory.additional_metadata["attachments"].append({
            "file_path": file_path,
            "attached_at": db.query(Memory).first().__table__.c.created_at.default.arg() if db.query(Memory).first() else None
        })

        db.commit()

        return {
            "success": True,
            "message": "File attached to memory",
            "memory_id": memory_id,
            "attachments": memory.additional_metadata.get("attachments", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attaching file to memory: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to attach file: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_files(
    days_old: int = Query(30, description="Delete files older than this many days"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Clean up old uploaded files

    Args:
        days_old: Delete files older than this many days
        container: Service container
        db: Database session

    Returns:
        Cleanup statistics
    """
    try:
        deleted_count = file_handler.cleanup_old_files(days_old=days_old)

        return {
            "success": True,
            "message": f"Cleaned up old files",
            "deleted_count": deleted_count,
            "days_old": days_old
        }

    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup files: {str(e)}"
        )
