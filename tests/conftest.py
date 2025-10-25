import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

@pytest.fixture(autouse=True)
async def setup_app():
    from app import database
    

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    database.client = client
    
  
    await db.users.delete_many({})
    await db.kyc_documents.delete_many({})
    await db.audit_logs.delete_many({})
    
    yield
    
 
    await db.users.delete_many({})
    await db.kyc_documents.delete_many({})
    await db.audit_logs.delete_many({})
    
    client.close()
