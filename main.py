from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, ForeignKey, String, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
    sessionmaker,
)


# database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    DATABASE_URL,
    echo=True,  # log SQL queries to the console for debugging
    connect_args={"check_same_thread": False} # needed for SQLite to allow multiple threads to access the database. Not needed for other databases like PostgreSQL or MySQL.
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# db models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models. Only used for type hinting."""
    pass

class Todo(Base):
    """
    SQLAlchemy model for a todo item.
    
    Has one TodoList
    """
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(255))
    completed: Mapped[bool] = mapped_column(default=False)
    todolist_id: Mapped[int] = mapped_column(ForeignKey("todolists.id"))

    # relationships
    todolist: Mapped["TodoList"] = relationship("TodoList", back_populates="todos")

class TodoList(Base):
    """
    SQLAlchemy model for a todo list.
    
    Has many Todo items
    """
    __tablename__ = "todolists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    # relationships
    todos: Mapped[list[Todo]] = relationship("Todo", back_populates="todolist")


# create tables in the database and start the FastAPI app
Base.metadata.create_all(engine)

app = FastAPI(title="Todo List API", description="A simple API for managing todo lists and items.")


# pydantic models aka schemas
class BaseSchema(BaseModel):
    """Base schema for Pydantic models"""
    model_config = ConfigDict(from_attributes=True)

class TodoCreate(BaseSchema):
    """Pydantic model for creating a todo item."""
    id: int | None = None # not required when creating a new todo item, but included in the response after creation
    description: str
    completed: bool = False
    todolist_id: int

class TodoListCreate(BaseSchema):
    """Pydantic model for creating a todo list."""
    id: int | None = None# not required when creating a new todo list, but included in the response after creation
    name: str


# dependency to get a database session for each request
def get_db():
    """Dependency that provides a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API endpoints
@app.get("/todolists/", response_model=list[TodoListCreate])
def read_todolists(db: Session = Depends(get_db)):
    """Endpoint to get all todo lists."""
    return db.execute(
        select(TodoList)
    ).scalars().all()

@app.post("/todolists/", response_model=TodoListCreate)
def create_todolist(todolist: TodoListCreate, db: Session = Depends(get_db)):
    """Endpoint to create a new todo list."""
    db_todolist = TodoList(name=todolist.name)
    db.add(db_todolist)
    db.commit()
    db.refresh(db_todolist)
    return db_todolist

@app.put("/todolists/{todolist_id}/", response_model=TodoListCreate)
def update_todolist(todolist_id: int, todolist: TodoListCreate, db: Session = Depends(get_db)):
    """Endpoint to update an existing todo list."""
    db_todolist = db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    ).scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    db_todolist.name = todolist.name
    db.commit()
    db.refresh(db_todolist)
    return db_todolist

@app.delete("/todolists/{todolist_id}/")
def delete_todolist(todolist_id: int, db: Session = Depends(get_db)):    
    """Endpoint to delete a todo list."""
    db_todolist = db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    ).scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    db.delete(db_todolist)
    db.commit()
    return {"detail": "Todo list deleted successfully"}

@app.get("/todolists/{todolist_id}/", response_model=list[TodoCreate])
def read_todos(todolist_id: int, db: Session = Depends(get_db)):
    """Endpoint to get all todo items for a specific todo list."""
    db_todolist = db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    ).scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    return db.execute(
        select(Todo).where(Todo.todolist_id == todolist_id)
    ).scalars().all()

@app.post("/todos/", response_model=TodoCreate)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Endpoint to create a new todo item."""
    # check if the specified todo list exists
    db_todolist = db.execute(
        select(TodoList).where(TodoList.id == todo.todolist_id)
    ).scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    
    db_todo = Todo(
        description=todo.description,
        completed=todo.completed,
        todolist_id=todo.todolist_id
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo  

@app.put("/todos/{todo_id}/", response_model=TodoCreate)
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    """Endpoint to update an existing todo item."""
    db_todo = db.execute(
        select(Todo).where(Todo.id == todo_id)
    ).scalars().first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found")
    
    # check if the specified todo list exists
    db_todolist = db.execute(
        select(TodoList).where(TodoList.id == todo.todolist_id)
    ).scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")

    db_todo.description = todo.description
    db_todo.completed = todo.completed
    db_todo.todolist_id = todo.todolist_id
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}/")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Endpoint to delete a todo item."""
    db_todo = db.execute(
        select(Todo).where(Todo.id == todo_id)
    ).scalars().first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found")
    db.delete(db_todo)
    db.commit()
    return {"detail": "Todo item deleted successfully"}

