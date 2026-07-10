import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream")
async def event_stream(current_user: User = Depends(get_current_user)):
    """Server-Sent Events endpoint for real-time job notifications.
    Connects to Redis pub/sub channel 'job_updates'.
    """
    async def generate():
        try:
            import redis as redis_lib
            from backend.config import settings
            r = redis_lib.from_url(settings.redis_url)
            pubsub = r.pubsub()
            pubsub.subscribe("job_updates")

            # Send initial heartbeat
            yield "event: connected\ndata: {}\n\n"

            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield f"data: {data}\n\n"
                else:
                    # Heartbeat every ~15 seconds to keep connection alive
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(5)
        except Exception:
            yield "event: error\ndata: {\"message\": \"Stream error\"}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
