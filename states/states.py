from aiogram.fsm.state import State, StatesGroup

class AddMovie(StatesGroup):
    code = State()
    title = State()
    description = State()
    genre = State()
    year = State()
    country = State()
    quality = State()
    poster = State()
    video = State()
    rating = State()

class AddChannel(StatesGroup):
    channel = State()

class DeleteMovie(StatesGroup):
    code = State()

class DeleteChannel(StatesGroup):
    channel = State()

class Search(StatesGroup):
    query = State()

class Broadcast(StatesGroup):
    content = State()

class EditMovie(StatesGroup):
    code = State()
    title = State()
    description = State()
    genre = State()
    year = State()
    country = State()
    quality = State()
    rating = State()
