from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Initialize FastAPI
app = FastAPI()

# Database Configuration
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    city = Column(String, nullable=False)
    status = Column(Boolean, default=False)  # Ensure status is part of User model

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for request validation & response
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone_number: str
    city: str

class UserResponse(BaseModel):
    name: str
    email: str
    phone_number: str
    city: str
    status: bool  # Include status in response

class ActivateUserRequest(BaseModel):
    email: EmailStr

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Signup endpoint
@app.post("/signup", response_model=UserResponse)
def signup(user: SignupRequest, db: Session = Depends(get_db)):
    # Check if the email is already registered
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered!")

    # Create a new user with status=False by default
    new_user = User(**user.dict(), status=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user  # Returning User model, including status

# Activate user endpoint (change status to True)
@app.post("/activate", response_model=UserResponse)
def activate_user(request: ActivateUserRequest, db: Session = Depends(get_db)):
    # Find the user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    if user.status:
        raise HTTPException(status_code=400, detail="User is already activated!")

    # Update status to True
    user.status = True
    db.commit()
    db.refresh(user)

    return user  # Returning updated user
