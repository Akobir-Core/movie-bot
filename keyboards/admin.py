from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino qo‘shish",callback_data="adm:add"),
         InlineKeyboardButton(text="🗑 Kino o‘chirish",callback_data="adm:del")],
        [InlineKeyboardButton(text="✏️ Kino tahrirlash",callback_data="adm:edit"),
         InlineKeyboardButton(text="📋 Kinolar",callback_data="adm:movies")],
        [InlineKeyboardButton(text="🔎 Kino qidirish",callback_data="adm:search")],
        [InlineKeyboardButton(text="📢 Kanal qo‘shish",callback_data="adm:addch"),
         InlineKeyboardButton(text="❌ Kanal o‘chirish",callback_data="adm:delch")],
        [InlineKeyboardButton(text="📋 Kanallar",callback_data="adm:channels")],
        [InlineKeyboardButton(text="📊 Statistika",callback_data="adm:stats"),
         InlineKeyboardButton(text="📈 Bot statistikasi",callback_data="adm:stats")],
        [InlineKeyboardButton(text="📢 Broadcast",callback_data="adm:broadcast")],
        [InlineKeyboardButton(text="⚙️ Bot sozlamalari",callback_data="adm:settings")],
    ])
