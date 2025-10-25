from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class KYCUpload(BaseModel):
    document_type: str  # "aadhar", "pan", "passport"
    document_number: str
    document_data: str  # simulated document data
