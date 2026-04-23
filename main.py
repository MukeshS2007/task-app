from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()
from database import engine, Base, SessionLocal
import models
from schemas import UserCreate, UserLogin
from auth import hash_password, verify_password, create_token
from database import Base
app = FastAPI()

Base.metadata.create_all(bind=engine)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- REGISTER ---------------- #
@app.post("/api/v1/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        email=user.email,
        password=hash_password(user.password),
        role="user"
    )

    db.add(new_user)
    db.commit()

    return {"msg": "User created successfully"}

# ---------------- LOGIN ---------------- #
@app.post("/api/v1/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_token({"sub": db_user.email})

    return {"access_token": token}

@app.get("/")
def home():
    return {"message": "API is running"}
@app.post("/api/v1/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(models.User).filter(models.User.email == user.email).first()

        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        new_user = models.User(
            email=user.email,
            password=hash_password(user.password),
            role="user"
        )

        db.add(new_user)
        db.commit()

        return {"msg": "User created successfully"}

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
from fastapi import Header
from jose import jwt
from schemas import UserCreate, UserLogin, TaskCreate

SECRET_KEY = "secret"
ALGORITHM = "HS256"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")

    user = db.query(models.User).filter(models.User.email == email).first()
    
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user
@app.get("/api/v1")
def root():
    return {"message": "API is working"}

@app.post("/api/v1/tasks")
def create_task(
    task: TaskCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_task = models.Task(
        title=task.title,
        description=task.description,
        owner_id=user.id
    )

    db.add(new_task)
    db.commit()

    return {"msg": "Task created"}

@app.get("/api/v1/tasks")
def get_tasks(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        tasks = db.query(models.Task).filter(models.Task.owner_id == user.id).all()
        return tasks
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/v1/tasks/{task_id}")
def delete_task(task_id: int,
                authorization: str = Header(None),
                db: Session = Depends(get_db)):

    user = get_current_user(authorization, db)

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(task)
    db.commit()

    return {"msg": "Deleted"}

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")

    user = db.query(models.User).filter(models.User.email == email).first()
    return user

@app.put("/api/v1/tasks/{task_id}")
def update_task(
    task_id: int,
    task: TaskCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if db_task.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db_task.title = task.title
    db_task.description = task.description

    db.commit()

    return {"msg": "Task updated"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)