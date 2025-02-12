from aiogram.fsm.state import StatesGroup, State

class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()