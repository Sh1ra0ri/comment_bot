from aiogram.fsm.state import State, StatesGroup


class RuleCreation(StatesGroup):
    name = State()
    keyword = State()
    message = State()


class RuleEdit(StatesGroup):
    waiting_value = State()


class AdminAdd(StatesGroup):
    waiting_id = State()