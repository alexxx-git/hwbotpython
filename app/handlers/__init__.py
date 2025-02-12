from aiogram import Router
from .profile import router as profile_router
from .water import router as water_router
from .food import router as food_router
from .workout import router as workout_router
from .progress import router as progress_router
from .misc import router as misc_router

def register_handlers(dp: Router):
    dp.include_router(profile_router)
    dp.include_router(water_router)
    dp.include_router(food_router)
    dp.include_router(workout_router)
    dp.include_router(progress_router)
    dp.include_router(misc_router)
