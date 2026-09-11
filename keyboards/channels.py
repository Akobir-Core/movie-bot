from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def subscription_keyboard(channels):
    rows=[]
    for c in channels:
        target=c["username"] or c["channel_id"]
        if not str(target).startswith("@") and str(target).lstrip("-").isdigit():
            url=f"https://t.me/c/{str(target).replace('-100','')}"
        else:
            url=f"https://t.me/{str(target).lstrip('@')}"
        rows.append([InlineKeyboardButton(text=f"📢 {c['title']}",url=url)])
    rows.append([InlineKeyboardButton(text="✅ Tekshirish",callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
