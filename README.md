# smartBank-Modular-Banking-Backend-System
Banking System


USE CASE - User Registration & KYC

1. # Featuures
- User registration with validation
- Secure JWT authentication
- KYC document upload
- MongoDB integration
  

# Actors can perform
1. Customer
-Register
-Login
-Upload KYC
-View own profile & KYC status

2. Auditor
-View pending KYC submissions
-Approve/Reject KYC
-View audit logs

# API Endpoints

Base URL: http://localhost:8000

# register User

1. Register
POST /auth/register
Request Body
{
  "email": "customer@example.com",
  "password": "securepass123",
  "name": "John Doe",
  "phone": "+919876543210"
}

Response
{
  "id": "671be123abc...",
  "message": "User registered successfully",
  "email": "customer@example.com",
  "role": "customer"
}

2. Login
POST /auth/login
Request Body

{
  "email": "customer@example.com",
  "password": "securepass123"
}


Response

{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

Customer Routes

3. Upload KYC
POST /kyc/upload
Headers: Authorization: Bearer <token>
Request Body

{
  "document_type": "aadhar",
  "document_number": "1234-5678-9012",
  "document_data": "base64_encoded_data_or_text"
}


Response

{
  "message": "KYC uploaded successfully",
  "kyc_id": "671bd890abc...",
  "status": "SUBMITTED"
}

4. View Profile
GET /users/me
Headers: Authorization: Bearer <token>
Response

{
  "id": "671be123abc...",
  "email": "customer@example.com",
  "name": "John Doe",
  "phone": "+919876543210",
  "role": "customer",
  "kyc_status": "SUBMITTED",
  "created_at": "2025-10-25T08:00:00.000Z"
}


5. View KYC Status
GET /users/me/kyc-status
Headers: Authorization: Bearer <token>
Response

{
  "kyc_status": "SUBMITTED"
}


#Auditor Routes

6. View Pending KYCs
GET /kyc/pending
Headers: Authorization: Bearer <auditor_token>
Response

[
  {
    "kyc_id": "671bd890abc...",
    "user_id": "671be123abc...",
    "user_name": "John Doe",
    "user_email": "customer@example.com",
    "document_type": "aadhar",
    "document_number": "1234-5678-9012",
    "submitted_at": "2025-10-25T09:30:00.000Z"
  }
]

7. View KYC Details
GET /kyc/{kyc_id}
Headers: Authorization: Bearer <auditor_token>
Response

{
  "kyc_id": "671bd890abc...",
  "user_id": "671be123abc...",
  "document_type": "aadhar",
  "document_number": "1234-5678-9012",
  "document_data": "base64_encoded_data_or_text",
  "status": "SUBMITTED",
  "submitted_at": "2025-10-25T09:30:00.000Z"
}


8. Approve KYC
PUT /kyc/{kyc_id}/approve
Headers: Authorization: Bearer <auditor_token>
Response

{
  "message": "KYC approved successfully"
}


9. Reject KYC
PUT /kyc/{kyc_id}/reject
Headers: Authorization: Bearer <auditor_token>
Response

{
  "message": "KYC rejected successfully"
}


1. Customer
POST /auth/register - Register
POST /auth/login - Login
POST /kyc/upload - Upload KYC
GET /users/me - Get profile
GET /users/me/kyc-status - Check KYC status

2. Auditor
GET /kyc/pending - View pending KYCs
GET /kyc/{kyc_id} - View KYC details
PUT /kyc/{kyc_id}/approve - Approve KYC
PUT /kyc/{kyc_id}/reject - Reject KYC

# FLOW
Customer Flow

2. 1. POST /auth/register
   ↓
2. POST /auth/login (get JWT token)
   ↓
3. POST /kyc/upload (with token)
   ↓
4. GET /users/me (check status)

Auditor Flow

1. POST /auth/login (with auditor credentials)
   ↓
2. GET /kyc/pending (view submissions)
   ↓
3. PUT /kyc/{id}/approve or /reject (future)

KYC Status

PENDING (default)
    ↓
SUBMITTED (after customer uploads)
    ↓
APPROVED/REJECTED (after auditor review - future)

# Actors Role
Customer:- Register, Login, Upload KYC, View own profile
Auditor:- Login, View pending KYCs, Approve/Reject KYCs


# Technology

Backend: FastAPI,
Database: MongoDB(Atlas)
Authentication: JWT
Testing: pytest, pytest-asyncio, pytest-cov 
Password Hashing: bcrypt
Validation: Pydantic
API Testing: Postman
server: Uvicorn
Environment Variables: python-dotenv
Code Editor: VS Code
Frontend(If Done): React.js

# Collections
1. user
2. kyc_doc
3. user_log

1. user schema
{
  "_id": ObjectId,                          
  "email": String,                           
  "password_hash": String,                   
  "name": String,                           
  "phone": String,                           
  "role": String,                            
  "kyc_status": String,                      
  "created_at": ISODate                      
}

2. kyc doc schema
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "document_type": "String",
  "document_number": "String",
  "document_data": "String",
  "status": "String",
  "reviewed_by": "ObjectId",
  "review_notes": "String",
  "submitted_at": "ISODate",
  "reviewed_at": "ISODate"
}

3. audit schema
   {
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "actor_id": "ObjectId",
  "action": "String",
  "actor_role": "String",
  "timestamp": "ISODate",
  "ip_address": "String",
  "details": {}
}

# Running the API

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/test_main.py -v

# Generate coverage report
pytest tests/test_main.py --cov=app --cov-report=html


