# 🖊️ TypeJaldi.com - Sketch Edition

TypeJaldi is a high-performance, distraction-free typing platform inspired by modern typing tools but with a unique, hand-drawn "sketchbook" aesthetic. It features real-time performance tracking, user levels, and a robust backend to save your progress.

## ✨ Features

- **Unique Aesthetics**: A premium "sketch" theme with doodle animations, notebook textures, and hand-drawn UI elements.
- **Multiple Test Modes**: Choose between 15s, 30s, 60s, and 120s typing tests.
- **Live Stats**: Real-time WPM (Words Per Minute), Accuracy, and Streak tracking.
- **Leveling System**: Earn XP for every test and level up from "Doodle Beginner" to "TypeJaldi Legend".
- **User Authentication**: Secure login and registration to save your history and best scores.
- **Responsive Design**: Works beautifully on both desktop and mobile devices.

## 🛠️ Technology Stack

- **Frontend**: Vanilla HTML5, CSS3 (with custom animations), and JavaScript.
- **Backend**: FastAPI (Python) - high performance and modern.
- **Database**: PostgreSQL with SQLAlchemy ORM.
- **Security**: JWT-based authentication with Bcrypt password hashing.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- PostgreSQL installed and running.

### 2. Environment Setup
Create a `.env` file in the `backend/` directory with the following variables:
```env
DATABASE_URL=postgresql://postgres:password@localhost/typejaldi
SECRET_KEY=your_random_secret_key_here
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Running the Project
From the root directory of the project, run the following command:

```bash
python -m uvicorn backend.main:app --reload
```

The application will be available at: **http://127.0.0.1:8000**

## 📂 Project Structure

- `index.html`: The main frontend application (Single Page App).
- `backend/`:
  - `main.py`: FastAPI application and API routes.
  - `models.py`: Database models (SQLAlchemy).
  - `schemas.py`: Pydantic data validation schemas.
  - `auth.py`: Authentication logic and JWT handling.
  - `database.py`: Database connection and session management.
  - `.env`: Environment variables (Database URL, Secret Key).

## 📝 License
This project is for personal use and development.
