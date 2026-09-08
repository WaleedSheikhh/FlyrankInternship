from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from app.database import engine, SessionLocal
from app.models import Base, Task
from sqlalchemy.orm import Session
from app.supabase_client import supabase

from app.schemas_auth import AuthCredentials
from fastapi import Header
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from app.auth_dependency import get_current_user
from fastapi.security import HTTPBearer

import os
from app.llm.schema import BookInput, EnrichmentOutput, Category
from openai import OpenAI

import json
import re
from pydantic import ValidationError


bearer_scheme = HTTPBearer()

print("Server running and connected to Supabase")

app = FastAPI()

Base.metadata.create_all(bind=engine)

db = SessionLocal()
if db.query(Task).count() == 0:
    db.add_all([
        Task(title="Buy milk", done=False),
        Task(title="Walk dog", done=True),
        Task(title="Write code", done=False),
    ])
    db.commit()
db.close()

llm_client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

@app.get("/")
def root():
    return {"name": "Tasks API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_status():
    return {"status": "OK"}


tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk dog", "done": True},
    {"id": 3, "title": "Write code", "done": False},
]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

class CreateTask(BaseModel):
    title: str

@app.post("/tasks", status_code=201)
def create_task(task: CreateTask, db: Session = Depends(get_db)):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    
    new_task = Task(title=task.title, done=False)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

class TaskUpdate(BaseModel):
    title: str
    done: bool

@app.put("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task.title = update.title
    task.done = update.done
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    db.delete(task)
    db.commit()

# added db browser and run queries there


@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result.user


@app.post("/auth/login")
def login(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        result = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token
    }


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


# @app.get("/protected/profile")
# def get_profile(authorization: str = Header(None)):
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Access token required")

#     token = authorization.split(" ")[1]

#     try:
#         user_response = supabase.auth.get_user(token)
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

#     user = user_response.user
#     return {
#         "id": user.id,
#         "email": user.email,
#         "created_at": user.created_at
#     }

@app.get("/protected/profile")
def get_profile(current=Depends(get_current_user)):
    user, token = current
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@app.get("/protected/dashboard")
def get_dashboard(current=Depends(get_current_user)):
    user, token = current
    return {"message": f"Welcome to your dashboard, {user.email}"}


@app.post("/auth/logout", status_code=204)
def logout(current=Depends(get_current_user)):
    user, token = current
    supabase.auth.sign_out()

@app.exception_handler(FastAPIHTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )



def load_prompt():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "prompts", "enrich-v1.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
    

def extract_json(text: str) -> str:
    # strip code fences if the model wrapped its answer in ```json ... ```
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return match.group(0)


def call_model(system_prompt: str, user_content: str) -> str:
    response = llm_client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content


@app.post("/enrich", response_model=EnrichmentOutput)
def enrich_book(book: BookInput):
    if os.getenv("LLM_STUB") == "1":
        return EnrichmentOutput(
            category=Category.other,
            summary="Stub response — no model called.",
            quality_flags=["stub_mode"]
        )

    system_prompt = load_prompt()
    user_content = book.model_dump_json()

    raw_text = call_model(system_prompt, user_content)

    try:
        json_str = extract_json(raw_text)
        parsed = json.loads(json_str)
        return EnrichmentOutput(**parsed)
    except (ValueError, json.JSONDecodeError, ValidationError) as e:
        # one repair retry — send the model its own mistake
        repair_message = (
            f"Your previous answer was rejected for this reason: {e}\n"
            f"Your previous answer was: {raw_text}\n"
            "Return only corrected JSON matching the schema."
        )
        response = llm_client.chat.completions.create(
            model=os.environ["LLM_MODEL"],
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": repair_message},
            ],
        )
        repaired_text = response.choices[0].message.content

        try:
            json_str = extract_json(repaired_text)
            parsed = json.loads(json_str)
            return EnrichmentOutput(**parsed)
        except (ValueError, json.JSONDecodeError, ValidationError) as e2:
            os.makedirs("logs", exist_ok=True)
            with open("logs/quarantine.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "input": book.model_dump(),
                    "raw_output": raw_text,
                    "repair_output": repaired_text,
                    "error": str(e2),
                    "prompt_version": "enrich-v1"
                }) + "\n")
            raise HTTPException(status_code=422, detail="Model output could not be validated after repair attempt")