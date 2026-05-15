from app.main import Todo, TodoList

def test_create_todolist(db_session):
    todolist = TodoList(name="Test Todo List")
    db_session.add(todolist)
    db_session.commit()
    db_session.refresh(todolist)

    assert todolist.id is not None
    assert todolist.name == "Test Todo List"

def test_edit_todolist(db_session):
    # First, create a todo list to edit
    todolist = TodoList(name="Test Todo List")
    db_session.add(todolist)
    db_session.commit()
    db_session.refresh(todolist)

    # Now, edit the created todo list
    todolist.name = "Updated Test Todo List"
    db_session.commit()
    db_session.refresh(todolist)

    assert todolist.name == "Updated Test Todo List"

def test_create_todo(db_session):
    # First, create a todo list to associate with the todo item
    todolist = TodoList(name="Test Todo List")
    db_session.add(todolist)
    db_session.commit()
    db_session.refresh(todolist)

    # Now, create a todo item associated with the created todo list
    todo = Todo(
        description="Test Todo Item",
        completed=False,
        todolist_id=todolist.id
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.id is not None
    assert todo.description == "Test Todo Item"
    assert todo.completed is False
    assert todo.todolist_id == todolist.id

def test_complete_todo(db_session):
    # First, create a todo list and a todo item to complete
    todolist = TodoList(name="Test Todo List")
    db_session.add(todolist)
    db_session.commit()
    db_session.refresh(todolist)

    todo = Todo(
        description="Test Todo Item",
        completed=False,
        todolist_id=todolist.id
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    # Now, mark the created todo item as completed
    todo.completed = True
    db_session.commit()
    db_session.refresh(todo)

    assert todo.completed is True