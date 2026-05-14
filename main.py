from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, String, select, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)



# database setup
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # log SQL queries to the console for debugging
)
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # prevent objects from being expired after commit
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
async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency that provides a database session for each request."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan function to create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # No cleanup needed on shutdown

app = FastAPI(
    title="Todo List API",
    description="A simple API for managing todo lists and items.",
    lifespan=lifespan
)


# API endpoints
@app.get("/todolists/", response_model=list[TodoListCreate])
async def read_todolists(db: AsyncSession = Depends(get_db)):
    """Endpoint to get all todo lists."""
    result = await db.execute(
        select(TodoList)
    )
    return result.scalars().all()

@app.post("/todolists/", response_model=TodoListCreate)
async def create_todolist(todolist: TodoListCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint to create a new todo list."""
    db_todolist = TodoList(name=todolist.name)
    db.add(db_todolist)
    await db.commit()
    await db.refresh(db_todolist)
    return db_todolist

@app.put("/todolists/{todolist_id}/", response_model=TodoListCreate)
async def update_todolist(todolist_id: int, todolist: TodoListCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint to update an existing todo list."""
    result = await db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    )
    db_todolist = result.scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    db_todolist.name = todolist.name
    await db.commit()
    await db.refresh(db_todolist)
    return db_todolist

@app.delete("/todolists/{todolist_id}/")
async def delete_todolist(todolist_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint to delete a todo list."""
    result = await db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    )
    db_todolist = result.scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    await db.delete(db_todolist)
    await db.commit()
    return {"detail": "Todo list deleted successfully"}

@app.get("/todolists/{todolist_id}/", response_model=list[TodoCreate])
async def read_todos(todolist_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint to get all todo items for a specific todo list."""
    result = await db.execute(
        select(TodoList).where(TodoList.id == todolist_id)
    )
    db_todolist = result.scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    result = await db.execute(
        select(Todo).where(Todo.todolist_id == todolist_id)
    )
    return result.scalars().all()

@app.post("/todos/", response_model=TodoCreate)
async def create_todo(todo: TodoCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint to create a new todo item."""
    # check if the specified todo list exists
    result = await db.execute(
        select(TodoList).where(TodoList.id == todo.todolist_id)
    )
    db_todolist = result.scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")
    
    db_todo = Todo(
        description=todo.description,
        completed=todo.completed,
        todolist_id=todo.todolist_id
    )
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo  

@app.put("/todos/{todo_id}/", response_model=TodoCreate)
async def update_todo(todo_id: int, todo: TodoCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint to update an existing todo item."""
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    db_todo = result.scalars().first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found")
    
    # check if the specified todo list exists
    result = await db.execute(
        select(TodoList).where(TodoList.id == todo.todolist_id)
    )
    db_todolist = result.scalars().first()
    if not db_todolist:
        raise HTTPException(status_code=404, detail="Todo list not found")

    db_todo.description = todo.description
    db_todo.completed = todo.completed
    db_todo.todolist_id = todo.todolist_id
    await db.commit()
    await db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}/")
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint to delete a todo item."""
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    db_todo = result.scalars().first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo item not found")
    await db.delete(db_todo)
    await db.commit()
    return {"detail": "Todo item deleted successfully"}

