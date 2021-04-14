from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class TaskCreation(StatesGroup):
    payment = State()
    location = State()
    time = State()
    contact = State()
    task_type = State()
    check_task = State()
    edit_task = State()


class TypeCreation(StatesGroup):
    name = State()
    difficulty = State()


type_deletion = State("type_deletion")
