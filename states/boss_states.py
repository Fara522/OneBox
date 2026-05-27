from aiogram.fsm.state import State, StatesGroup


class BossLogin(StatesGroup):
    waiting_login = State()
    waiting_password = State()


class BossAddAdmin(StatesGroup):
    full_name = State()
    login = State()
    password = State()


class BossAddCustomer(StatesGroup):
    full_name = State()


class BossDeleteAdmin(StatesGroup):
    confirm = State()


class BossDeleteCustomer(StatesGroup):
    confirm = State()
