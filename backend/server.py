from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt

# Import rule engine
from rule_engine import compute_allocation, analyze_expenses, generate_insights

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlanRequest(BaseModel):
    salary: float
    age: int
    riskLevel: str  # "Low", "Medium", "High"
    expenses: Dict[str, float]  # groceries, rent, utilities, etc.

class PlanResponse(BaseModel):
    recommendedPlan: Dict[str, Any]
    actualSummary: Dict[str, Any]
    comparison: Dict[str, Any]
    insights: List[str]

class Tip(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dailyTip: str
    microLessons: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupportRequest(BaseModel):
    name: str
    email: EmailStr
    message: str

class SupportRequestDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        raise e
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Auth Routes
@api_router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(name=user_data.name, email=user_data.email)
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['password_hash'] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create token
    token = create_token(user.id, user.email)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user['id'], user['email'])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {"id": user['id'], "name": user['name'], "email": user['email']}
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "name": current_user['name'],
        "email": current_user['email']
    }

# Plan Route
@api_router.post("/plan", response_model=PlanResponse)
async def create_plan(plan_req: PlanRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Compute allocation
        allocation = compute_allocation(
            salary=plan_req.salary,
            age=plan_req.age,
            risk_level=plan_req.riskLevel
        )
        
        # Analyze expenses
        analysis = analyze_expenses(
            salary=plan_req.salary,
            expenses=plan_req.expenses
        )
        
        # Generate insights
        insights = generate_insights(
            allocation=allocation,
            analysis=analysis,
            expenses=plan_req.expenses
        )
        
        # Save plan to database
        plan_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user['id'],
            "salary": plan_req.salary,
            "age": plan_req.age,
            "riskLevel": plan_req.riskLevel,
            "expenses": plan_req.expenses,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.plans.insert_one(plan_doc)
        
        return {
            "recommendedPlan": allocation,
            "actualSummary": analysis["actualSummary"],
            "comparison": analysis["comparison"],
            "insights": insights
        }
    except Exception as e:
        logging.error(f"Error in create_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")

# Tips Route
@api_router.get("/tips")
async def get_tips():
    # Get random tip from database
    tips = await db.tips.find({}, {"_id": 0}).to_list(100)
    if tips:
        import random
        tip = random.choice(tips)
        return tip
    else:
        # Return default tip if none in DB
        return {
            "dailyTip": "Track your daily expenses to stay within budget.",
            "microLessons": [
                "Start with the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
                "Build an emergency fund covering 3-6 months of expenses.",
                "Invest early to benefit from compound interest."
            ]
        }

# Support Route
@api_router.post("/support", status_code=status.HTTP_201_CREATED)
async def create_support_request(support_req: SupportRequest):
    support_doc = SupportRequestDB(**support_req.model_dump())
    doc = support_doc.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.support_requests.insert_one(doc)
    
    return {"message": "Support request submitted successfully", "id": support_doc.id}

# Health Check
@api_router.get("/health")
async def health_check():
    return {"status": "ok"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
