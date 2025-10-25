from fastapi import FastAPI, HTTPException, Depends, Header
from app.database import connect_db, close_db, get_db
from app.models import UserRegister, UserLogin, Token, KYCUpload
from fastapi.middleware.cors import CORSMiddleware
from app.auth import hash_password, verify_password, create_token, decode_token
from datetime import datetime
from bson import ObjectId
import logging

app = FastAPI(title="SmartBank API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Registration logic

@app.on_event("startup")
async def startup():
    await connect_db()
    logging.info("App started and DB connected")

@app.on_event("shutdown")
async def shutdown():
    await close_db()
    logging.info("App shutdown and DB closed")

# Get Profile

async def get_current_user(authorization: str = Header(None)):
    """Extract and verify user from JWT token"""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        
        payload = decode_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return payload
        
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/auth/register", status_code=201)
async def register(user: UserRegister):
    """Register new customer"""
    db = get_db()
    
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = hash_password(user.password)
    
    user_doc = {
        "email": user.email,
        "password_hash": hashed_password,
        "name": user.name,
        "phone": user.phone,
        "role": "customer",
        "kyc_status": "PENDING",
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "User registered successfully",
        "email": user.email,
        "role": "customer"
    }

@app.get("/")
async def root():
    return {"message": "SmartBank API - User Registration"}


#Login 

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    """Login for customer and auditor"""
    db = get_db()
    
    found_user = await db.users.find_one({"email": user.email})
    
    if not found_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(user.password, found_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(
        email=found_user["email"],
        user_id=str(found_user["_id"]),
        role=found_user["role"]
    )
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }

    #Get profile

@app.get("/users/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """GET: Get current user's profile (protected route)"""
    db = get_db()
    
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "phone": user["phone"],
        "role": user["role"],
        "kyc_status": user["kyc_status"],
        "created_at": user["created_at"]
    }


#KYC upload

@app.post("/kyc/upload")
async def upload_kyc(kyc: KYCUpload, current_user: dict = Depends(get_current_user)):
    """POST: Upload KYC document (Customer only)"""
    
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Only customers can upload KYC")
    
    db = get_db()
    
    kyc_doc = {
        "user_id": ObjectId(current_user["user_id"]),
        "document_type": kyc.document_type,
        "document_number": kyc.document_number,
        "document_data": kyc.document_data,
        "status": "SUBMITTED",
        "submitted_at": datetime.utcnow()
    }
    
    result = await db.kyc_documents.insert_one(kyc_doc)
    
    await db.users.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"kyc_status": "SUBMITTED"}}
    )
    
    return {
        "message": "KYC uploaded successfully",
        "kyc_id": str(result.inserted_id),
        "status": "SUBMITTED"
    }

    # AUDITOR ROLE

@app.get("/kyc/pending")
async def get_pending_kycs(current_user: dict = Depends(get_current_user)):
    """GET: View pending KYC submissions (Auditor only)"""
    
    if current_user["role"] != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can view pending KYCs")
    
    db = get_db()
    
    kycs = await db.kyc_documents.find({"status": "SUBMITTED"}).to_list(100)
    
    result = []
    for kyc in kycs:
        user = await db.users.find_one({"_id": kyc["user_id"]})
        result.append({
            "kyc_id": str(kyc["_id"]),
            "user_id": str(kyc["user_id"]),
            "user_name": user["name"],
            "user_email": user["email"],
            "document_type": kyc["document_type"],
            "document_number": kyc["document_number"],
            "submitted_at": kyc["submitted_at"]
        })
    
    return result


@app.put("/kyc/{kyc_id}/approve")
async def approve_kyc(kyc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can approve KYC")
    
    db = get_db()
    kyc = await db.kyc_documents.find_one({"_id": ObjectId(kyc_id)})
    
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    
    await db.kyc_documents.update_one(
        {"_id": ObjectId(kyc_id)},
        {"$set": {
            "status": "APPROVED",
            "reviewed_by": ObjectId(current_user["user_id"]),
            "reviewed_at": datetime.utcnow()
        }}
    )
    
    await db.users.update_one(
        {"_id": kyc["user_id"]},
        {"$set": {"kyc_status": "APPROVED"}}
    )
    
    await db.audit_logs.insert_one({
        "user_id": kyc["user_id"],
        "actor_id": ObjectId(current_user["user_id"]),
        "action": "KYC_APPROVED",
        "actor_role": "auditor",
        "timestamp": datetime.utcnow(),
        "details": {"kyc_id": kyc_id}
    })
    
    return {"message": "KYC approved successfully"}


@app.put("/kyc/{kyc_id}/reject")
async def reject_kyc(kyc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "auditor":
        raise HTTPException(status_code=403, detail="Only auditors can reject KYC")
    
    db = get_db()
    kyc = await db.kyc_documents.find_one({"_id": ObjectId(kyc_id)})
    
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    
    await db.kyc_documents.update_one(
        {"_id": ObjectId(kyc_id)},
        {"$set": {
            "status": "REJECTED",
            "reviewed_by": ObjectId(current_user["user_id"]),
            "reviewed_at": datetime.utcnow()
        }}
    )
    
    await db.users.update_one(
        {"_id": kyc["user_id"]},
        {"$set": {"kyc_status": "REJECTED"}}
    )
    
    await db.audit_logs.insert_one({
        "user_id": kyc["user_id"],
        "actor_id": ObjectId(current_user["user_id"]),
        "action": "KYC_REJECTED",
        "actor_role": "auditor",
        "timestamp": datetime.utcnow(),
        "details": {"kyc_id": kyc_id}
    })
    
    return {"message": "KYC rejected successfully"}

