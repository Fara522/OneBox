from aiogram.fsm.state import State, StatesGroup


class AdminLogin(StatesGroup):
    waiting_login = State()
    waiting_password = State()


class AdminAddWorker(StatesGroup):
    full_name = State()
    age = State()


class AdminDeleteMachine(StatesGroup):
    confirm = State()


class AdminAddMachine(StatesGroup):
    name = State()
    description = State()


class AdminAssignMachine(StatesGroup):
    select_worker = State()
    select_machine = State()


class AdminDeleteWorker(StatesGroup):
    confirm = State()


class AdminEditWorker(StatesGroup):
    select_worker = State()
    new_value = State()
