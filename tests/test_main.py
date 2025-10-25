import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login_success():
    """Test successful register and login flow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        register_resp = await client.post("/auth/register", json={
            "email": "user1@test.com",
            "password": "test123",
            "name": "User One",
            "phone": "+919000000001"
        })
        assert register_resp.status_code == 201
        login_resp = await client.post("/auth/login", json={
            "email": "user1@test.com",
            "password": "test123"
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()


@pytest.mark.asyncio
async def test_login_failure_wrong_password():
    """Test login failure due to wrong password"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        await client.post("/auth/register", json={
            "email": "user2@test.com",
            "password": "correctpass",
            "name": "User Two",
            "phone": "+919000000002"
        })
        # Attempt login with wrong password
        response = await client.post("/auth/login", json={
            "email": "user2@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_kyc_upload_and_view_profile():
    """Test KYC upload and profile retrieval with updated status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        reg_resp = await client.post("/auth/register", json={
            "email": "user3@test.com",
            "password": "test123",
            "name": "User Three",
            "phone": "+919000000003"
        })
        token = (await client.post("/auth/login", json={
            "email": "user3@test.com",
            "password": "test123"
        })).json()["access_token"]
        
        # Upload KYC
        upload_resp = await client.post(
            "/kyc/upload",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_type": "aadhar",
                "document_number": "1234-5678-9012",
                "document_data": "dummydata"
            }
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["status"] == "SUBMITTED"

        # Get profile
        profile_resp = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_resp.status_code == 200
        assert profile_resp.json()["kyc_status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_auditor_role_access():
    """Test auditor role can view KYCs, but cannot upload"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create auditor
        await client.post("/auth/register", json={
            "email": "auditor@test.com",
            "password": "auditor123",
            "name": "Auditor",
            "phone": "+919000000010"
        })
        # Change role in DB to auditor manually
        from app.database import get_db
        db = get_db()
        await db.users.update_one({"email": "auditor@test.com"}, {"$set": {"role": "auditor"}})

        # Login as auditor
        auditor_token = (await client.post("/auth/login", json={
            "email": "auditor@test.com",
            "password": "auditor123"
        })).json()["access_token"]

        # Auditor tries to upload KYC - should fail
        upload_resp = await client.post(
            "/kyc/upload",
            headers={"Authorization": f"Bearer {auditor_token}"},
            json={
                "document_type": "pan",
                "document_number": "ABCDE1234F",
                "document_data": "dummy_pan"
            }
        )
        assert upload_resp.status_code == 403

        # Auditor views pending KYCs
        pending_resp = await client.get(
            "/kyc/pending",
            headers={"Authorization": f"Bearer {auditor_token}"}
        )
        assert pending_resp.status_code == 200
        assert isinstance(pending_resp.json(), list)
