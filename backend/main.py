import os
from dotenv import load_dotenv
import secrets
from datetime import datetime, timedelta, timezone

# Define BASE_DIR (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Load .env from the backend directory
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth, database, email_utils
from .database import engine, get_db
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
import httpx

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TypeJaldi API")

# Session middleware (needed for OAuth state)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "typejaldi-super-secret-sketch-key-2026")
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── OAuth Setup ──────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# ─── Static / Root ────────────────────────────────────
@app.get("/login")
def get_login():
    return FileResponse(os.path.join(BASE_DIR, "login.html"))

@app.get("/")
def read_root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# ─── Register ─────────────────────────────────────────
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if db_user:
        if db_user.email == user.email and not db_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already linked to a Google account. Please use 'Sign in with Google' or use 'Forgot Password' to set a secret key."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username or email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password_hash=hashed_password,
    )
    db.add(new_user)
    db.flush()  # To get new_user.id

    # Create associated records
    db.add(models.UserProfile(user_id=new_user.id))
    db.add(models.UserStats(user_id=new_user.id))
    
    db.commit()
    db.refresh(new_user)
    return new_user

# ─── Login ────────────────────────────────────────────
@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.username == user_credentials.username_or_email) |
        (models.User.email  == user_credentials.username_or_email)
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    
    if not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="This account uses Google Login. Please use 'Sign in with Google' or use 'Forgot Password' to set a secret key.",
                            headers={"WWW-Authenticate": "Bearer"})
    if not auth.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

# ─── Google OAuth ─────────────────────────────────────
@app.get("/auth/google")
async def google_login(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback/google")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {exc}")

    userinfo = token.get("userinfo") or {}
    google_id = userinfo.get("sub")
    email     = userinfo.get("email")
    name      = userinfo.get("name", "")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Could not retrieve Google profile info")

    # Find or create user
    user = db.query(models.User).filter(models.User.google_id == google_id).first()
    if not user:
        # Try finding by email
        user = db.query(models.User).filter(models.User.email == email).first()
        if user:
            user.google_id = google_id
            user.full_name = user.full_name or name
            db.commit()
        else:
            # Generate a unique username from email
            base_username = email.split("@")[0][:40]
            username = base_username
            suffix = 1
            while db.query(models.User).filter(models.User.username == username).first():
                username = f"{base_username}_{suffix}"
                suffix += 1

            user = models.User(
                username=username,
                email=email,
                full_name=name,
                google_id=google_id,
                is_verified=True,
            )
            db.add(user)
            db.flush()  # Get user ID

    # Ensure associated records exist
    if not db.query(models.UserProfile).filter(models.UserProfile.user_id == user.id).first():
        db.add(models.UserProfile(user_id=user.id))
    if not db.query(models.UserStats).filter(models.UserStats.user_id == user.id).first():
        db.add(models.UserStats(user_id=user.id))
    
    db.commit()
    db.refresh(user)

    access_token = auth.create_access_token(data={"sub": user.username})
    return RedirectResponse(
        url=f"{FRONTEND_URL}/?token={access_token}&username={user.username}"
    )

# ─── Test Results ─────────────────────────────────────
@app.post("/test-results", status_code=status.HTTP_201_CREATED)
def save_test_result(
    result: schemas.TestResultCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    new_result = models.TestResult(
        user_id=current_user.id,
        wpm=result.wpm,
        raw_wpm=result.raw_wpm,
        accuracy=result.accuracy,
        mode=result.mode,
        duration=result.duration,
    )
    db.add(new_result)

    stats = db.query(models.UserStats).filter(models.UserStats.user_id == current_user.id).first()
    if not stats:
        stats = models.UserStats(user_id=current_user.id)
        db.add(stats)
    
    stats.total_tests += 1
    if result.wpm > stats.best_wpm:
        stats.best_wpm = result.wpm
    stats.avg_wpm = (float(stats.avg_wpm) * (stats.total_tests - 1) + result.wpm) / stats.total_tests
    stats.avg_accuracy = (float(stats.avg_accuracy) * (stats.total_tests - 1) + result.accuracy) / stats.total_tests
    
    # Calculate XP: similar logic to frontend
    # awardXP(netWPM, accuracy, effectiveTime * 60, bestStreak)
    # Since we don't have streak here, we use a base multiplier
    accuracy_factor = result.accuracy / 100
    time_multiplier = max(0.2, min(2, result.duration / 60))
    base_xp = result.wpm * accuracy_factor * time_multiplier
    earned_xp = max(3, int(base_xp))
    stats.total_xp += earned_xp

    db.commit()
    return {"message": "Result saved successfully", "earned_xp": earned_xp}

# ─── Me (get current user info) ───────────────────────
@app.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    # Calculate level: 1 level per 5 tests (or we could use XP logic)
    # Let's stick to the frontend threshold logic or a simpler version here
    # If we want exact match with frontend, we should return XP and let frontend calculate
    total_tests = current_user.stats.total_tests if current_user.stats else 0
    current_user.level = (total_tests // 5) + 1
    return current_user

# ─── Forgot Password ──────────────────────────────────
@app.post("/forgot-password")
async def forgot_password(request: schemas.ForgotPassword, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        # We return 200 even if user doesn't exist for security (don't leak emails)
        return {"message": "If this email is registered, you will receive a reset link shortly."}
    
    # Generate token
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    
    # Send actual email as a background task
    reset_link = f"{FRONTEND_URL}/reset-password?reset_token={token}"
    background_tasks.add_task(email_utils.send_reset_email, user.email, user.username, reset_link)
    
    return {"message": "If this email is registered, you will receive a reset link shortly."}

@app.post("/reset-password")
async def reset_password(request: schemas.ResetPassword, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.reset_token == request.token,
        models.User.reset_token_expiry > datetime.now(timezone.utc)
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    user.password_hash = auth.get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    
    return {"message": "Password updated successfully! You can now login."}

@app.get("/reset-password")
async def get_reset_page():
    return FileResponse(os.path.join(BASE_DIR, "reset-password.html"))
