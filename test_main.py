from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_todo_response(description: str = "Learn FastAPI", todolist_id: int = 1):
    response = client.post(
        "/todos",
        json={"description": description, "todolist_id": todolist_id},
    )
    assert response.status_code == 200
    return response.json()


def create_todolist_response(name: str = "My Todo List"):
    response = client.post(
        "/todolists",
        json={"name": name},
    )
    assert response.status_code == 200
    return response.json()


def test_create_todo():
    # requires a todo list, so we create it first
    todolist_response = create_todolist_response(name="My Todo List")
    todolist_id = todolist_response["id"]
    
    title = "Learn FastAPI"
    data = create_todo_response(description=title, todolist_id=todolist_id)

    assert data["description"] == title


def test_update_todo():
    # First, create a new todolist and a new todo item to update
    todolist_response = create_todolist_response(name="My Todo List")
    todolist_id = todolist_response["id"]
    data = create_todo_response(description="Learn FastAPI", todolist_id=todolist_id)
    todo_id = data["id"]

    # Now, update the created todo item
    response = client.put(
        f"/todos/{todo_id}",
        json={
            "description": "Learn FastAPI - Updated",
            "completed": True,
            "todolist_id": todolist_id
        },
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["description"] == "Learn FastAPI - Updated"
    assert updated_data["completed"] is True


def test_delete_todo():
    # First, create a new todo item in a new todo list to delete
    todolist_response = create_todolist_response(name="My Todo List")
    todolist_id = todolist_response["id"]
    
    description = "Learn FastAPI"

    data = create_todo_response(description=description, todolist_id=todolist_id)
    todo_id = data["id"]

    # Now, delete the created todo item
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Todo item deleted successfully"}

    # Verify that the todo item has been deleted    
    response = client.get(f"/todolists/{todolist_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(todo["id"] != todo_id for todo in response.json())


def test_update_nonexistent_todo():
    response = client.put(
        "/todos/9999",  # Assuming this ID does not exist
        json={
            "description": "Nonexistent Todo", 
            "completed": False,
            "todolist_id": 1  # Assuming this todo list exists,
        },
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo item not found"}


def test_post_todolists():
    # Create a new todo list
    name = "My Todo List"
    data = create_todolist_response(name=name)
    assert data["name"] == name


def test_get_todolists():
    response = client.get("/todolists")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_todolist():
    # First, create a new todo list to update
    name = "My Todo List"
    data = create_todolist_response(name=name)
    todolist_id = data["id"]

    # Now, update the created todo list
    new_name = "Updated Todo List"
    response = client.put(
        f"/todolists/{todolist_id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["name"] == new_name


def test_delete_todolist():
    # First, create a new todo list to delete
    name = "My Todo List"
    data = create_todolist_response(name=name)
    todolist_id = data["id"]

    # Now, delete the created todo list
    response = client.delete(f"/todolists/{todolist_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Todo list deleted successfully"}

    # Verify that the todo list has been deleted    
    response = client.get(f"/todolists/{todolist_id}")
    assert response.status_code == 404


def test_get_nonexistent_todolist():
    response = client.get("/todolists/9999")  # Assuming this ID does not exist
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo list not found"}


def test_update_nonexistent_todolist():
    response = client.put(
        "/todolists/9999",  # Assuming this ID does not exist
        json={"name": "Nonexistent Todo List"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo list not found"}


def test_get_todos_for_todolist():
    # First, create a new todo list
    name = "My Todo List"
    data = create_todolist_response(name=name)
    todolist_id = data["id"]

    # Now, get the todos for the created todo list (should be empty)
    response = client.get(f"/todolists/{todolist_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0

    # add a new todo item to the created todo list
    description = "Learn FastAPI"
    completed = False
    data = create_todo_response(description=description, todolist_id=todolist_id)
    todo_id = data["id"]

    # Now, get the todos for the created todo list (should contain the new todo)
    response = client.get(f"/todolists/{todolist_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == todo_id