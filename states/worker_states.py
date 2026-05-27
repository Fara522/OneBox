from aiogram.fsm.state import State, StatesGroup


class WorkerRegister(StatesGroup):
    select_name = State()


class WorkerOrder(StatesGroup):
    select_machine = State()
    working = State()


class WorkerStartOrder(StatesGroup):
    enter_helper = State()
