import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import redis.asyncio as aioredis
from typing import Dict

router = APIRouter(prefix="/api/ws", tags=["websockets"])

# A simple connection manager is optional if we rely strictly on Redis Pub/Sub per socket,
# but it's good practice. We can just yield from Redis pubsub directly in the endpoint.

@router.websocket("/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    from api.utils.redis_utils import get_redis_url
    redis_url = get_redis_url()
    redis = await aioredis.from_url(redis_url)
    pubsub = redis.pubsub()
    
    channel_name = f"session_progress_{session_id}"
    await pubsub.subscribe(channel_name)
    
    try:
        while True:
            # We use a small timeout so we can also check if the client disconnected
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                data = message["data"].decode("utf-8")
                await websocket.send_text(data)
                
                # If analysis is complete or errored, we can optionally close
                parsed = json.loads(data)
                if parsed.get("step") in ["Analysis Complete", "ERROR"]:
                    break
            
            # Brief yield to event loop
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from {channel_name}")
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis.close()
        try:
            await websocket.close()
        except Exception:
            pass

@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(None)):
    print(f"[WS] New connection attempt with token: {token[:10] if token else None}...")
    await websocket.accept()
    
    if not token:
        print("[WS] Missing token, closing.")
        await websocket.close(code=1008, reason="Missing token")
        return
        
    from api.auth.jwt_handler import decode_access_token
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        print("[WS] Invalid or expired token, closing.")
        await websocket.close(code=1008, reason="Invalid token")
        return
        
    user_id = payload.get("sub")
    print(f"[WS] Authenticated user {user_id}. Connecting to Redis...")
    
    try:
        from api.utils.redis_utils import get_redis_url
        redis_url = get_redis_url()
        redis = await aioredis.from_url(redis_url)
        pubsub = redis.pubsub()
        
        channel_name = f"user_notifications:{user_id}"
        await pubsub.subscribe(channel_name)
        print(f"[WS] Subscribed to {channel_name}")
    except Exception as e:
        print(f"[WS] Failed to connect to Redis: {e}")
        await websocket.close(code=1011, reason="Internal Server Error")
        return
    
    try:
        while True:
            # We use a small timeout so we can also check if the client disconnected
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                data = message["data"].decode("utf-8")
                await websocket.send_text(data)
                
            # Brief yield to event loop
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from {channel_name}")
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis.close()
        try:
            await websocket.close()
        except Exception:
            pass
