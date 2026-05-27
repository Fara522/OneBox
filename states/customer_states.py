from aiogram.fsm.state import State, StatesGroup


class CustomerOrder(StatesGroup):
    enter_product = State()
    enter_quantity = State()
    enter_comment = State()
