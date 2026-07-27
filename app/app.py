from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from app.database import engine, SessionLocal
from app.models import Base, Task
from sqlalchemy.orm import Session

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

@app.post("/tasks")
def add_task(task: CreateTask):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is Required")

    new_id = max((task["id"] for task in tasks), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

class TaskUpdate(BaseModel):
    title: str
    done: bool

@app.put("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = update.title
            task["done"] = update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")