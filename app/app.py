from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_status():
    return {"status": "OK"}


tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk dog", "done": True},
    {"id": 3, "title": "Write code", "done": False},
]


@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{tasks.id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

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