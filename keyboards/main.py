from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎬 Kino qidirish"), KeyboardButton(text="🔥 Top kinolar")],
        [KeyboardButton(text="🆕 Yangi kinolar"), KeyboardButton(text="🎭 Janrlar")],
        [KeyboardButton(text="🔎 Kod orqali izlash"), KeyboardButton(text="❤️ Sevimlilar")],
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="ℹ️ Bot haqida")]
    ], resize_keyboard=True)

def back_home():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")]
    ], resize_keyboard=True)

def movie_list(movies):
    rows=[]
    for m in movies:
        rows.append([InlineKeyboardButton(text=f"🎬 {m['title']} · {m['code']}",
                                          callback_data=f"movie:{m['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def movie_actions(movie_id, favorite=False):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💔 Sevimlidan olish" if favorite else "❤️ Sevimlilarga",
                              callback_data=f"fav:{movie_id}")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home")]
    ])

def genres():
    items=["Drama","Komediya","Action","Horror","Romance","Fantasy","Sci-Fi","Thriller","Animation","Adventure"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎭 {g}",callback_data=f"genre:{g}") for g in items[i:i+2]]
        for i in range(0,len(items),2)
    ])
