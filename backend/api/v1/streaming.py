"""Streaming endpoints for real-time message and AI response streaming"""

import logging
import asyncio
import json
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.main import get_container
from backend.core.container import ServiceContainer
from backend.db.models import Session as DBSession, Message
from backend.core.engine import PAIEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


async def stream_ai_response(
    message_content: str,
    session_id: str,
    user_id: str,
    engine: PAIEngine,
    db: Session
) -> AsyncGenerator[str, None]:
    """Stream AI response from Claude API

    Args:
        message_content: User message content
        session_id: Session ID
        user_id: User ID
        engine: PAI engine instance
        db: Database session

    Yields:
        JSON-encoded chunks of response
    """
    try:
        # Get session
        db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not db_session:
            yield json.dumps({
                "error": "Session not found",
                "status": "error"
            }).encode() + b'\n'
            return

        # Build context from conversation history
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()

        context_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[-10:]  # Last 10 messages for context
        ]
        context_messages.append({"role": "user", "content": message_content})

        # Stream from Claude API
        full_response = ""
        chunk_count = 0

        try:
            # Use synchronous client wrapped in async context
            # Note: In production, use async Anthropic client when available
            response = engine.client.messages.create(
                model=engine.model,
                max_tokens=1024,
                system="You are PAI, a helpful personal AI assistant. Provide concise, helpful responses.",
                messages=context_messages,
                stream=True
            )

            # Stream the response
            for event in response:
                chunk_count += 1

                # Extract content delta
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    chunk_text = event.delta.text
                    full_response += chunk_text

                    # Send chunk to client
                    yield json.dumps({
                        "type": "content_block_delta",
                        "delta": {
                            "type": "text_delta",
                            "text": chunk_text
                        },
                        "index": chunk_count
                    }).encode() + b'\n'

                    # Yield control to allow other coroutines to run
                    await asyncio.sleep(0)

                # Handle message completion
                elif hasattr(event, 'type') and event.type == 'message_stop':
                    yield json.dumps({
                        "type": "message_stop",
                        "status": "complete"
                    }).encode() + b'\n'

            # Store AI response in database
            ai_message = Message(
                id=str(uuid4()),
                session_id=session_id,
                sender="pai",
                sender_id=engine.model,
                content=full_response,
                role="assistant",
                created_at=datetime.utcnow()
            )
            db.add(ai_message)
            db.commit()

            logger.info(f"Streamed response: {len(full_response)} chars in {chunk_count} chunks")

        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            yield json.dumps({
                "error": str(e),
                "status": "error"
            }).encode() + b'\n'

    except Exception as e:
        logger.error(f"Error in stream_ai_response: {str(e)}")
        yield json.dumps({
            "error": str(e),
            "status": "error"
        }).encode() + b'\n'


@router.get("/sessions/{session_id}/messages")
async def stream_session_messages(
    session_id: str,
    user_message: str = Query(..., description="User message to respond to"),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(lambda: container.db_session)
):
    """Stream AI response for a session message (SSE endpoint)

    Args:
        session_id: Session ID
        user_message: User message content
        container: Service container
        db: Database session

    Returns:
        StreamingResponse with SSE-formatted chunks
    """
    try:
        # Validate session
        db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get engine
        engine = container.engine

        # Return streaming response
        return StreamingResponse(
            stream_ai_response(
                message_content=user_message,
                session_id=session_id,
                user_id=db_session.user_id,
                engine=engine,
                db=db
            ),
            media_type="application/x-ndjson"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming session messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error streaming response: {str(e)}"
        )


@router.get("/health/stream")
async def stream_health_check():
    """Stream health check (for testing SSE)

    Returns:
        StreamingResponse with health status updates
    """
    async def health_stream() -> AsyncGenerator[str, None]:
        try:
            for i in range(5):
                status = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "check": i + 1
                }
                yield json.dumps(status).encode() + b'\n'
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in health stream: {str(e)}")

    return StreamingResponse(
        health_stream(),
        media_type="application/x-ndjson"
    )


# Import needed modules
from uuid import uuid4
from datetime import datetime

__all__ = ["router", "stream_ai_response"]
