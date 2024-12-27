import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import bot_token, city_search, five_days_forecast

bot = Bot(token=bot_token)
storage = MemoryStorage()

dp = Dispatcher(storage=storage, bot=bot)


class WeatherFSM(StatesGroup):
    waiting_cities = State()
    waiting_time = State()


class TimeCallback(CallbackData, prefix="time"):
    days: int


@dp.message(Command('start'))
async def start_handler(message: Message):
    await message.answer("Привет, я бот, который предоставляет информацию о погоде по нескольким точкам!")


@dp.message(Command('help'))
async def help_handler(message: Message):
    await message.answer(
        "Список доступных команд:\n"
        "/start - начать работу\n"
        "/help - получить список команд\n"
        "/weather - получить прогноз погоды по нескольким точкам\n"
    )


@dp.message(Command('weather'))
async def weather_handler(message: Message, state: FSMContext):
    await message.answer("Введите названия городов на отдельных строчках: ")
    await state.set_state(WeatherFSM.waiting_cities)


@dp.message(WeatherFSM.waiting_cities)
async def cities_input_handler(message: Message, state: FSMContext):
    cities = list(x.strip() for x in message.text.split("\n") if x.strip())
    if len(cities) < 2:
        await message.answer("Введите не менее 2-х городов.")
        return
    await state.update_data(cities=cities)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="2 дня", callback_data=TimeCallback(days=2).pack()))
    builder.row(InlineKeyboardButton(text="3 дня", callback_data=TimeCallback(days=3).pack()))
    builder.row(InlineKeyboardButton(text="4 дня", callback_data=TimeCallback(days=4).pack()))
    builder.row(InlineKeyboardButton(text="5 дней", callback_data=TimeCallback(days=5).pack()))
    await message.answer("Теперь выберите временной промежуток:", reply_markup=builder.as_markup())
    await state.set_state(WeatherFSM.waiting_time)


@dp.callback_query(TimeCallback.filter())
async def callback_handler(callback: CallbackQuery, callback_data: TimeCallback, state: FSMContext):
    days = callback_data.days
    data = await state.get_data()
    cities = data.get('cities', [])
    keys = {city: city_search(city=city) for city in cities}
    weathers = {city: five_days_forecast(keys[city])[:2 * days] for city in cities}
    for city, weather in weathers.items():
        msg = f'Город: {city}\n'
        for ind, item in enumerate(weather):
            day = ind // 2 + 1
            day_part = 'День' if ind % 2 == 0 else 'Ночь'
            msg += (f'День {day} | {day_part}\n'
                    f'Температура: {round(item.temperature, 1)}\n'
                    f'Влажность: {round(item.humidity, 1)}\n'
                    f'Скорость ветра: {round(item.wind_speed, 1)}\n\n')
        await callback.message.answer(msg)
    await state.clear()


if __name__ == "__main__":
    await dp.start_polling(bot)

