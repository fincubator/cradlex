from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class Registration(StatesGroup):
    first_message = State()
    contact = State()


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


class WorkerCreation(StatesGroup):
    name = State()
    phone = State()
    skill = State()
    check_worker = State()
    edit_worker = State()


type_deletion = State("type_deletion")
task_photo = State("task_photo")
