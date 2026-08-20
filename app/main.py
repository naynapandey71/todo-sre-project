from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# --- Database setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/tododb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class TodoModel(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# --- API setup ---
app = FastAPI(title="Todo API")

class TodoCreate(BaseModel):
    title: str

class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Used later by Docker/Kubernetes/monitoring to check if the app is alive."""
    return {"status": "ok"}

@app.get("/todos", response_model=list[TodoOut])
def list_todos():
    db = SessionLocal()
    todos = db.query(TodoModel).all()
    db.close()
    return todos

@app.post("/todos", response_model=TodoOut)
def create_todo(todo: TodoCreate):
    db = SessionLocal()
    new_todo = TodoModel(title=todo.title, done=False)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    db.close()
    return new_todo

@app.put("/todos/{todo_id}/complete", response_model=TodoOut)
def complete_todo(todo_id: int):
    db = SessionLocal()
    todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if not todo:
        db.close()
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.done = True
    db.commit()
    db.refresh(todo)
    db.close()
    return todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    db = SessionLocal()
    todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if not todo:
        db.close()
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    db.close()
    return {"message": "deleted"}