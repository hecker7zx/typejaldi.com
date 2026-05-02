from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth, database
from .database import engine, get_db

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TypeJaldi API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.post("/test-results", status_code=status.HTTP_201_CREATED)
def save_test_result(result: schemas.TestResultCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    new_result = models.TestResult(
        user_id=current_user.id,
        wpm=result.wpm,
        raw_wpm=result.raw_wpm,
        accuracy=result.accuracy,
        mode=result.mode,
        duration=result.duration
    )
    db.add(new_result)
    
    # Update user stats
    stats = db.query(models.UserStats).filter(models.UserStats.user_id == current_user.id).first()
    if stats:
        stats.total_tests += 1
        if result.wpm > stats.best_wpm:
            stats.best_wpm = result.wpm
        # Simple moving average for avg_wpm and accuracy
        stats.avg_wpm = (stats.avg_wpm * (stats.total_tests - 1) + result.wpm) / stats.total_tests
        stats.avg_accuracy = (stats.avg_accuracy * (stats.total_tests - 1) + result.accuracy) / stats.total_tests
    
    db.commit()
    return {"message": "Result saved successfully"}

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Hash password
    hashed_password = auth.get_password_hash(user.password)
    
    # Create new user
    new_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # Find user by username or email
    user = db.query(models.User).filter(
        (models.User.username == user_credentials.username_or_email) | 
        (models.User.email == user_credentials.username_or_email)
    ).first()
    
    if not user or not auth.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}
