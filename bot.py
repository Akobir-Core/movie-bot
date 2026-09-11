import asyncio
import logging
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, OWNER_IDS, DATABASE_PATH
from database import Database
from states.states import AddMovie, AddChannel, DeleteMovie, DeleteChannel, Search, Broadcast, EditMovie
from keyboards.main import main_menu, back_home, movie_list, movie_actions, genres
from keyboards.admin import admin_menu
from keyboards.channels import subscription_keyboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
db=Database(DATABASE_PATH)
dp=Dispatcher()

def is_admin(user_id): return user_id in OWNER_IDS

async def safe_answer(call, text=None):
    try:
        await call.answer(text or "")
    except Exception:
        pass

async def subscribed(bot, user_id):
    channels=db.channels()
    if not channels:
        return True
    for c in channels:
        try:
            member=await bot.get_chat_member(c["channel_id"], user_id)
            if member.status in {ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR,ChatMemberStatus.CREATOR}:
                continue
            return False
        except Exception:
            return False
    return True

async def require_sub(message, bot):
    if await subscribed(bot,message.from_user.id):
        return True
    await message.answer("🔒 Kino olishdan oldin quyidagi kanallarga obuna bo‘ling:",reply_markup=subscription_keyboard(db.channels()))
    return False

async def send_movie(target, bot, movie):
    caption=(
        f"🎬 <b>{escape(movie['title'])}</b>\n\n"
        f"🔢 Kod: <code>{escape(movie['code'])}</code>\n"
        f"📅 Yil: {escape(movie['year'] or '-')}\n"
        f"🌍 Davlat: {escape(movie['country'] or '-')}\n"
        f"🎭 Janr: {escape(movie['genre'] or '-')}\n"
        f"⭐ Reyting: {movie['rating'] or 0}\n"
        f"🎞 Sifat: {escape(movie['quality'] or '-')}\n\n"
        f"📝 {escape(movie['description'] or '-')}"
    )
    if movie["poster_file_id"]:
        await bot.send_photo(target, movie["poster_file_id"], caption=caption,
                             reply_markup=movie_actions(movie["id"],db.is_favorite(target,movie["id"])))
    else:
        await bot.send_message(target,caption,reply_markup=movie_actions(movie["id"],db.is_favorite(target,movie["id"])))
    await bot.send_video(target,movie["video_file_id"],caption=f"🎬 {escape(movie['title'])}")

@dp.message(CommandStart())
async def start(message: Message, state:FSMContext):
    await state.clear()
    db.upsert_user(message.from_user)
    await message.answer(
        "🎬 <b>KINO BOT</b>\n\nKino kodini yuboring yoki menyudan kerakli bo‘limni tanlang.",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def admin_cmd(message:Message,state:FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi yo‘q.")
        return
    await message.answer("🛠 <b>ADMIN PANEL</b>",reply_markup=admin_menu())

@dp.message(Command("add"))
async def add_cmd(message:Message,state:FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi yo‘q."); return
    await state.clear(); await state.set_state(AddMovie.code)
    await message.answer("🎬 Kino kodini yuboring:",reply_markup=back_home())

@dp.callback_query(F.data=="check_sub")
async def check_sub(call:CallbackQuery,bot:Bot):
    if await subscribed(bot,call.from_user.id):
        await safe_answer(call,"✅ Obuna tasdiqlandi!")
        await call.message.answer("✅ Hammasi joyida. Endi kino kodini yuboring.",reply_markup=main_menu())
    else:
        await safe_answer(call,"❌ Hali barcha kanallarga obuna bo‘lmagansiz.")

@dp.callback_query(F.data=="home")
async def home(call:CallbackQuery):
    await safe_answer(call)
    await call.message.answer("🏠 Bosh menyu",reply_markup=main_menu())

@dp.message(F.text=="🏠 Bosh menyu")
async def home_msg(message:Message,state:FSMContext):
    await state.clear(); await message.answer("🏠 Bosh menyu",reply_markup=main_menu())

@dp.message(F.text=="⬅️ Orqaga")
async def back_msg(message:Message,state:FSMContext):
    await state.clear(); await message.answer("⬅️ Orqaga",reply_markup=main_menu())

# /add flow
@dp.message(AddMovie.code)
async def add_code(message:Message,state:FSMContext):
    if db.get_movie(message.text.strip()):
        await message.answer("❌ Bu kod allaqachon mavjud. Boshqa kod yuboring."); return
    await state.update_data(code=message.text.strip()); await state.set_state(AddMovie.title)
    await message.answer("🎬 Kino nomini yuboring:")

@dp.message(AddMovie.title)
async def add_title(message:Message,state:FSMContext):
    await state.update_data(title=message.text.strip()); await state.set_state(AddMovie.description)
    await message.answer("📝 Qisqacha tavsif yuboring:")

@dp.message(AddMovie.description)
async def add_desc(message:Message,state:FSMContext):
    await state.update_data(description=message.text.strip()); await state.set_state(AddMovie.genre)
    await message.answer("🎭 Janrini yuboring:")

@dp.message(AddMovie.genre)
async def add_genre(message:Message,state:FSMContext):
    await state.update_data(genre=message.text.strip()); await state.set_state(AddMovie.year)
    await message.answer("📅 Yilni yuboring:")

@dp.message(AddMovie.year)
async def add_year(message:Message,state:FSMContext):
    await state.update_data(year=message.text.strip()); await state.set_state(AddMovie.country)
    await message.answer("🌍 Davlatni yuboring:")

@dp.message(AddMovie.country)
async def add_country(message:Message,state:FSMContext):
    await state.update_data(country=message.text.strip()); await state.set_state(AddMovie.quality)
    await message.answer("🎞 Sifat/formatni yuboring (masalan: 1080p, WEB-DL):")

@dp.message(AddMovie.quality)
async def add_quality(message:Message,state:FSMContext):
    await state.update_data(quality=message.text.strip()); await state.set_state(AddMovie.poster)
    await message.answer("🖼 Poster rasmini yuboring:")

@dp.message(AddMovie.poster, F.photo)
async def add_poster(message:Message,state:FSMContext):
    await state.update_data(poster_file_id=message.photo[-1].file_id); await state.set_state(AddMovie.video)
    await message.answer("🎥 Kino video faylini yuboring:")

@dp.message(AddMovie.poster)
async def add_poster_bad(message:Message):
    await message.answer("❌ Iltimos, poster rasmini yuboring.")

@dp.message(AddMovie.video, F.video)
async def add_video(message:Message,state:FSMContext):
    await state.update_data(video_file_id=message.video.file_id); await state.set_state(AddMovie.rating)
    await message.answer("⭐ Reytingni yuboring (masalan: 8.5) yoki 0:")

@dp.message(AddMovie.video, F.document)
async def add_document_video(message:Message,state:FSMContext):
    await state.update_data(video_file_id=message.document.file_id); await state.set_state(AddMovie.rating)
    await message.answer("⭐ Reytingni yuboring (masalan: 8.5) yoki 0:")

@dp.message(AddMovie.video)
async def add_video_bad(message:Message):
    await message.answer("❌ Iltimos, video fayl yuboring.")

@dp.message(AddMovie.rating)
async def add_rating(message:Message,state:FSMContext):
    try: rating=float(message.text.strip().replace(",","."))
    except ValueError: await message.answer("❌ Reyting raqam bo‘lishi kerak."); return
    data=await state.get_data(); data["rating"]=rating
    try:
        db.add_movie(data)
    except Exception as e:
        logging.exception("Movie add error")
        await message.answer("❌ Kino saqlashda xatolik yuz berdi.")
        await state.clear(); return
    await state.clear()
    await message.answer(f"✅ Kino muvaffaqiyatli qo‘shildi!\n\n🎬 {escape(data['title'])}\n🔢 {escape(data['code'])}",reply_markup=admin_menu())

# User search / code
@dp.message(F.text=="🎬 Kino qidirish")
async def search_start(message:Message,state:FSMContext):
    await state.set_state(Search.query); await message.answer("🔎 Kino nomi, kodi yoki janrini yozing:",reply_markup=back_home())

@dp.message(F.text=="🔎 Kod orqali izlash")
async def code_search_start(message:Message,state:FSMContext):
    await state.set_state(Search.query); await message.answer("🔢 Kino kodini yuboring:",reply_markup=back_home())

@dp.message(Search.query)
async def search_state(message:Message,state:FSMContext):
    if not await require_sub(message,message.bot): return
    q=message.text.strip(); db.register_search(message.from_user.id,q)
    movie=db.get_movie(q)
    if movie:
        db.register_view(message.from_user.id,movie["id"])
        await send_movie(message.chat.id,message.bot,movie); await state.clear(); return
    movies=db.search_movies(q)
    if not movies: await message.answer("❌ Bunday kino topilmadi."); return
    await message.answer("🔎 Natijalar:",reply_markup=movie_list(movies)); await state.clear()

@dp.message(F.text)
async def text_router(message:Message):
    db.upsert_user(message.from_user)
    if message.text=="🔥 Top kinolar":
        await message.answer("🔥 <b>TOP 10 KINO</b>",reply_markup=movie_list(db.top_movies()))
    elif message.text=="🆕 Yangi kinolar":
        await message.answer("🆕 <b>YANGI KINOLAR</b>",reply_markup=movie_list(db.new_movies()))
    elif message.text=="🎭 Janrlar":
        await message.answer("🎭 Janrni tanlang:",reply_markup=genres())
    elif message.text=="❤️ Sevimlilar":
        await message.answer("❤️ Sevimli kinolaringiz:",reply_markup=movie_list(db.favorites(message.from_user.id)))
    elif message.text=="👤 Profil":
        u=db.get_user(message.from_user.id); s=db.stats()
        await message.answer(
            f"👤 <b>Profil</b>\n\n"
            f"🧑 Ism: {escape(u['full_name'])}\n🆔 ID: <code>{u['id']}</code>\n"
            f"🎬 Ko‘rgan: {u['views_count']}\n❤️ Sevimli: {len(db.favorites(u['id']))}\n"
            f"🔎 Qidiruv: {u['search_count']}\n📅 Qo‘shilgan: {escape(u['joined_at'][:10])}",
            reply_markup=back_home())
    elif message.text=="📊 Statistika":
        s=db.stats()
        await message.answer(f"📊 <b>Bot statistikasi</b>\n\n👥 Foydalanuvchilar: {s['users']}\n🎬 Kinolar: {s['movies']}\n📺 Ko‘rishlar: {s['views']}\n🔎 Qidiruvlar: {s['searches']}")
    elif message.text=="ℹ️ Bot haqida":
        await message.answer("ℹ️ <b>KINO BOT</b>\n\nKino kodlari orqali tezkor qidiruv, janrlar, top kinolar va sevimlilar tizimi.")
    elif message.text.strip():
        if await require_sub(message,message.bot):
            movie=db.get_movie(message.text.strip())
            if movie:
                db.register_view(message.from_user.id,movie["id"]); await send_movie(message.chat.id,message.bot,movie)
            else:
                await message.answer("❌ Bunday kino topilmadi.")

@dp.callback_query(F.data.startswith("movie:"))
async def movie_callback(call:CallbackQuery,bot:Bot):
    if not await subscribed(bot,call.from_user.id):
        await safe_answer(call,"❌ Avval kanallarga obuna bo‘ling."); await call.message.answer("🔒 Majburiy obuna:",reply_markup=subscription_keyboard(db.channels())); return
    movie=db.conn.execute("SELECT * FROM movies WHERE id=?", (int(call.data.split(":")[1]),)).fetchone()
    if not movie: await safe_answer(call,"❌ Kino topilmadi."); return
    db.register_view(call.from_user.id,movie["id"]); await safe_answer(call)
    await send_movie(call.message.chat.id,bot,movie)

@dp.callback_query(F.data.startswith("fav:"))
async def favorite_callback(call:CallbackQuery):
    mid=int(call.data.split(":")[1]); ok=db.toggle_favorite(call.from_user.id,mid)
    await safe_answer(call,"❤️ Sevimlilarga qo‘shildi" if ok else "💔 Sevimlidan olib tashlandi")
    try:
        await call.message.edit_reply_markup(reply_markup=movie_actions(mid,ok))
    except Exception: pass

@dp.callback_query(F.data.startswith("genre:"))
async def genre_callback(call:CallbackQuery):
    genre=call.data.split(":",1)[1]; movies=db.genre_movies(genre)
    await safe_answer(call)
    await call.message.answer(f"🎭 <b>{escape(genre)}</b>",reply_markup=movie_list(movies) if movies else None)
    if not movies: await call.message.answer("❌ Bu janrda kino topilmadi.")

# Admin callbacks
@dp.callback_query(F.data.startswith("adm:"))
async def admin_callback(call:CallbackQuery,state:FSMContext):
    if not is_admin(call.from_user.id): await safe_answer(call,"⛔ Ruxsat yo‘q."); return
    action=call.data.split(":")[1]; await safe_answer(call)
    if action=="add":
        await state.clear(); await state.set_state(AddMovie.code); await call.message.answer("🎬 Kino kodini yuboring:")
    elif action=="del":
        await state.clear(); await state.set_state(DeleteMovie.code); await call.message.answer("🗑 O‘chiriladigan kino kodini yuboring:")
    elif action=="edit":
        await state.clear(); await state.set_state(EditMovie.code); await call.message.answer("✏️ Tahrirlanadigan kino kodini yuboring:")
    elif action=="movies":
        ms=db.all_movies(); await call.message.answer("📋 Kinolar:",reply_markup=movie_list(ms) if ms else None)
    elif action=="search":
        await state.clear(); await state.set_state(Search.query); await call.message.answer("🔎 Qidiruv so‘zini yuboring:")
    elif action=="addch":
        await state.clear(); await state.set_state(AddChannel.channel); await call.message.answer("📢 Kanal username (@channel) yoki ID sini yuboring:")
    elif action=="delch":
        await state.clear(); await state.set_state(DeleteChannel.channel); await call.message.answer("❌ O‘chiriladigan kanal username yoki ID sini yuboring:")
    elif action=="channels":
        cs=db.channels()
        if not cs: await call.message.answer("📋 Kanallar ro‘yxati bo‘sh.")
        else: await call.message.answer("📋 <b>Majburiy kanallar</b>\n\n" + "\n".join(
            f"{i}. {escape(c['title'])} — {escape(c['username'] or c['channel_id'])}" for i,c in enumerate(cs,1)))
    elif action=="stats":
        s=db.stats(); await call.message.answer(
            f"📊 <b>STATISTIKA</b>\n\n👥 Jami foydalanuvchilar: {s['users']}\n"
            f"🎬 Jami kinolar: {s['movies']}\n📺 Jami ko‘rishlar: {s['views']}\n"
            f"🔎 Qidiruvlar: {s['searches']}\n📢 Majburiy kanallar: {s['channels']}\n🟢 Faol (7 kun): {s['active']}")
    elif action=="broadcast":
        await state.clear(); await state.set_state(Broadcast.content); await call.message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni yuboring:")
    elif action=="settings":
        await call.message.answer("⚙️ Sozlamalar: kanal va kontent boshqaruvi admin panel orqali amalga oshiriladi.")

@dp.message(DeleteMovie.code)
async def delete_movie(message:Message,state:FSMContext):
    if not is_admin(message.from_user.id): return
    ok=db.delete_movie(message.text.strip()); await state.clear()
    await message.answer("✅ Kino o‘chirildi." if ok else "❌ Bunday kino topilmadi.",reply_markup=admin_menu())

@dp.message(DeleteChannel.channel)
async def delete_channel(message:Message,state:FSMContext):
    if not is_admin(message.from_user.id): return
    value=message.text.strip()
    found=None
    for c in db.channels():
        if value==str(c["channel_id"]) or value.lower()==str(c["username"] or "").lower():
            found=c; break
    ok=db.delete_channel(found["channel_id"]) if found else False
    await state.clear(); await message.answer("✅ Kanal o‘chirildi." if ok else "❌ Kanal topilmadi.",reply_markup=admin_menu())

@dp.message(AddChannel.channel)
async def add_channel(message:Message,state:FSMContext):
    if not is_admin(message.from_user.id): return
    value=message.text.strip()
    try:
        chat=await message.bot.get_chat(value)
        db.add_channel(chat.id, chat.username and "@"+chat.username, chat.title or chat.full_name or str(chat.id))
        await state.clear()
        await message.answer(f"✅ Kanal qo‘shildi!\n\n📢 {escape(chat.title or '-')}\n🆔 <code>{chat.id}</code>\n🔗 @{escape(chat.username or '-')}",reply_markup=admin_menu())
    except Exception:
        await message.answer("❌ Kanalni topib bo‘lmadi. Botni kanalga administrator qilib qo‘shing va @username yoki -100... ID yuboring.")

@dp.message(Broadcast.content, F.content_type.in_({ContentType.TEXT,ContentType.PHOTO,ContentType.VIDEO,ContentType.DOCUMENT}))
async def broadcast(message:Message,state:FSMContext):
    if not is_admin(message.from_user.id): return
    ids=db.all_user_ids(); sent=0; failed=0
    for uid in ids:
        try:
            await message.bot.copy_message(uid,message.chat.id,message.message_id)
            sent+=1
            await asyncio.sleep(0.04)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after+1)
            try: await message.bot.copy_message(uid,message.chat.id,message.message_id); sent+=1
            except Exception: failed+=1
        except (TelegramForbiddenError,TelegramBadRequest): failed+=1
        except Exception: failed+=1
    await state.clear()
    await message.answer(f"📢 <b>Broadcast tugadi</b>\n\n✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}",reply_markup=admin_menu())

# Edit flow: text fields only, keeps media intact.
@dp.message(EditMovie.code)
async def edit_code(message:Message,state:FSMContext):
    m=db.get_movie(message.text.strip())
    if not m: await message.answer("❌ Kino topilmadi."); return
    await state.update_data(movie_id=m["id"]); await state.set_state(EditMovie.title); await message.answer(f"🎬 Yangi nom ({m['title']}):")

@dp.message(EditMovie.title)
async def edit_title(message:Message,state:FSMContext):
    await state.update_data(title=message.text.strip()); await state.set_state(EditMovie.description); await message.answer("📝 Yangi tavsif:")

@dp.message(EditMovie.description)
async def edit_desc(message:Message,state:FSMContext):
    await state.update_data(description=message.text.strip()); await state.set_state(EditMovie.genre); await message.answer("🎭 Yangi janr:")

@dp.message(EditMovie.genre)
async def edit_genre(message:Message,state:FSMContext):
    await state.update_data(genre=message.text.strip()); await state.set_state(EditMovie.year); await message.answer("📅 Yangi yil:")

@dp.message(EditMovie.year)
async def edit_year(message:Message,state:FSMContext):
    await state.update_data(year=message.text.strip()); await state.set_state(EditMovie.country); await message.answer("🌍 Yangi davlat:")

@dp.message(EditMovie.country)
async def edit_country(message:Message,state:FSMContext):
    await state.update_data(country=message.text.strip()); await state.set_state(EditMovie.quality); await message.answer("🎞 Yangi sifat:")

@dp.message(EditMovie.quality)
async def edit_quality(message:Message,state:FSMContext):
    await state.update_data(quality=message.text.strip()); await state.set_state(EditMovie.rating); await message.answer("⭐ Yangi reyting:")

@dp.message(EditMovie.rating)
async def edit_rating(message:Message,state:FSMContext):
    try: rating=float(message.text.strip().replace(",","."))
    except ValueError: await message.answer("❌ Reyting raqam bo‘lishi kerak."); return
    data=await state.get_data(); data["rating"]=rating
    db.update_movie(data["movie_id"],data); await state.clear()
    await message.answer("✅ Kino ma’lumotlari yangilandi.",reply_markup=admin_menu())

async def main():
    bot=Bot(BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Kino bot ishga tushdi.")
        await dp.start_polling(bot)
    finally:
        db.close()
        await bot.session.close()

if __name__=="__main__":
    asyncio.run(main())
