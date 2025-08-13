#!/usr/bin/env python3
"""Минимальный тест системы"""

print("1. Testing imports...")

try:
    import os
    import sys
    print("✅ Basic imports OK")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    sys.exit(1)

try:
    from memory.in_memory_store import InMemoryStore
    print("✅ InMemoryStore imported")
except Exception as e:
    print(f"❌ InMemoryStore import failed: {e}")

try:
    from agents.base import BaseAgent
    print("✅ BaseAgent imported")
except Exception as e:
    print(f"❌ BaseAgent import failed: {e}")

try:
    from tools.smart_groupchat import SmartGroupChatManager
    print("✅ SmartGroupChatManager imported")
except Exception as e:
    print(f"❌ SmartGroupChatManager import failed: {e}")

print("\n2. Testing Redis fallback...")
try:
    from memory.redis_store import RedisStore
    store = RedisStore(use_fallback=True)
    store.set("test", "value")
    value = store.get("test")
    print(f"✅ Redis fallback works: {value}")
except Exception as e:
    print(f"❌ Redis fallback failed: {e}")

print("\n3. Testing simple API endpoint...")
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    
    app = FastAPI()
    
    class TestResponse(BaseModel):
        status: str
        message: str
    
    @app.get("/test", response_model=TestResponse)
    async def test():
        return TestResponse(status="ok", message="Test successful")
    
    print("✅ FastAPI test endpoint created")
    
except Exception as e:
    print(f"❌ FastAPI test failed: {e}")

print("\n✅ All tests completed!")