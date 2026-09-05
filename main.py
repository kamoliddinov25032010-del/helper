import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

from config import BOT_TOKEN, ADMIN_ID
from db import create_table, add_attendance, get_today
from users import add_user, delete_user, is_registered, get_all_users, update_name
from voice_limit import (
    can_send_voice,
    increment_voice_count,
    has_warned_today,
    mark_warned,
    VOICE_LIMIT,
    set_pending_voice,
    get_pending_voice,
    clear_pending_voice,
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

waiting_id = False
waiting_name = False
waiting_delete_id = False
pending_user_id = None


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ ID biriktirish")],
        [KeyboardButton(text="🗑 Foydalanuvchini o'chirish")],
        [KeyboardButton(text="📋 Bugungi ro'yxat")]
    ],
    resize_keyboard=True
)


def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Tasdiqlash")]],
        resize_keyboard=True
    )


def voice_decision_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Adminga yuborish", callback_data="voice_send")],
        [
            InlineKeyboardButton(text="🔄 Qayta urinish", callback_data="voice_retry"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data="voice_cancel")
        ]
    ])


@dp.errors()
async def global_error_handler(event):
    # Har qanday kutilmagan xatoni faqat konsolga yozadi, botni to'xtatmaydi
    print(f"⚠️ Kutilmagan xato: {event.exception}")
    return True


@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        await message.answer("👨‍💻 Admin panel", reply_markup=admin_keyboard)
        return

    if not is_registered(user_id):
        await message.answer("❌ Siz hali ro'yxatdan o'tmagansiz.")
        return

    update_name(user_id, message.from_user.full_name)

    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 Foydalanuvchi botga kirdi (/start bosdi)\n\n"
            f"👤 Ism: {message.from_user.full_name}\n"
            f"🔗 Username: {username}\n"
            f"🆔 Telegram ID: {user_id}"
        )
    except Exception as e:
        print(f"⚠️ Adminga xabar yuborilmadi: {e}")

    await message.answer(
        f"Assalomu alaykum 👋\n\n"
        f"Tasdiqlash uchun tugmani bosing:",
        reply_markup=confirm_keyboard()
    )


@dp.message(F.text == "➕ ID biriktirish")
async def add_button(message: Message):
    global waiting_id

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("Telegram ID yuboring:")
    waiting_id = True


@dp.message(F.text == "🗑 Foydalanuvchini o'chirish")
async def delete_button(message: Message):
    global waiting_delete_id

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("O'chirmoqchi bo'lgan Telegram ID yuboring:")
    waiting_delete_id = True


@dp.message(F.text == "✅ Tasdiqlash")
async def confirm(message: Message):
    user_id = message.from_user.id

    if not is_registered(user_id):
        return

    saved = add_attendance(user_id)

    if saved:
        await message.answer("✅ Tasdiq qabul qilindi")

        now = datetime.now()
        username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

        try:
            await bot.send_message(
                ADMIN_ID,
                f"✅ Yangi tasdiq!\n\n"
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🔗 Username: {username}\n"
                f"🆔 Telegram ID: {user_id}\n"
                f"📅 Sana: {now.strftime('%d.%m.%Y')}\n"
                f"⏰ Vaqt: {now.strftime('%H:%M')}"
            )
        except Exception as e:
            print(f"⚠️ Adminga xabar yuborilmadi: {e}")
    else:
        await message.answer("ℹ️ Siz bugun allaqachon tasdiqlagansiz.")


@dp.message(F.text == "📋 Bugungi ro'yxat")
async def today(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()
    today_data = get_today()

    checked = [telegram_id for telegram_id, time in today_data]

    text = "📋 Bugungi ro'yxat:\n\n"

    for user_id, info in users.items():
        name = info["name"]
        status = "🟢 Tasdiqlagan" if int(user_id) in checked else "🔴 Tasdiqlamagan"
        text += f"👤 {name}\n🆔 {user_id}\n{status}\n\n"

    await message.answer(text)


@dp.message(F.voice)
async def voice_message(message: Message):
    user_id = message.from_user.id

    if not is_registered(user_id):
        return

    if not can_send_voice(user_id):
        await message.answer(
            f"⛔ Siz bugungi limitga yetdingiz ({VOICE_LIMIT}/{VOICE_LIMIT} ta ovozli xabar)."
        )
        return

    if not has_warned_today(user_id):
        mark_warned(user_id)
        await message.answer(
            f"ℹ️ Diqqat: kuniga faqat {VOICE_LIMIT} martagacha ovozli xabar yuborishingiz mumkin."
        )

    # Yangi ovoz kelsa, avvalgi qaror kutilayotgan ovozning o'rnini bosadi
    set_pending_voice(user_id, message.voice.file_id)

    await message.answer(
        "✅ Ovozli xabaringiz qabul qilindi. Nima qilishni tanlaysiz?",
        reply_markup=voice_decision_keyboard()
    )


@dp.callback_query(F.data.in_({"voice_send", "voice_retry", "voice_cancel"}))
async def voice_decision(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data

    try:
        await callback.answer()
    except Exception:
        pass

    if action == "voice_cancel":
        clear_pending_voice(user_id)
        try:
            await callback.message.edit_text("🗑 Bekor qilindi.")
        except Exception:
            await callback.message.answer("🗑 Bekor qilindi.")
        return

    if action == "voice_retry":
        clear_pending_voice(user_id)
        try:
            await callback.message.edit_text("🔄 Yangi ovozli xabaringizni yuboring:")
        except Exception:
            await callback.message.answer("🔄 Yangi ovozli xabaringizni yuboring:")
        return

    if action == "voice_send":
        file_id = get_pending_voice(user_id)

        if not file_id:
            try:
                await callback.message.edit_text("❌ Ovozli xabar topilmadi, qaytadan yuboring.")
            except Exception:
                await callback.message.answer("❌ Ovozli xabar topilmadi, qaytadan yuboring.")
            return

        if not can_send_voice(user_id):
            try:
                await callback.message.edit_text(
                    f"⛔ Siz bugungi limitga yetdingiz ({VOICE_LIMIT}/{VOICE_LIMIT} ta ovozli xabar)."
                )
            except Exception:
                await callback.message.answer(
                    f"⛔ Siz bugungi limitga yetdingiz ({VOICE_LIMIT}/{VOICE_LIMIT} ta ovozli xabar)."
                )
            clear_pending_voice(user_id)
            return

        username = f"@{callback.from_user.username}" if callback.from_user.username else "yo'q"
        now = datetime.now()

        await bot.send_voice(
            ADMIN_ID,
            file_id,
            caption=(
                f"🎤 Yangi ovozli xabar!\n\n"
                f"👤 Ism: {callback.from_user.full_name}\n"
                f"🔗 Username: {username}\n"
                f"🆔 Telegram ID: {user_id}\n"
                f"📅 Sana: {now.strftime('%d.%m.%Y')}\n"
                f"⏰ Vaqt: {now.strftime('%H:%M')}"
            )
        )

        sent_count = increment_voice_count(user_id)
        clear_pending_voice(user_id)

        try:
            await callback.message.edit_text(
                f"📤 Ovozli xabar adminga yuborildi. ({sent_count}/{VOICE_LIMIT})"
            )
        except Exception:
            await callback.message.answer(
                f"📤 Ovozli xabar adminga yuborildi. ({sent_count}/{VOICE_LIMIT})"
            )


@dp.message()
async def messages(message: Message):
    global waiting_id, waiting_name, waiting_delete_id, pending_user_id

    if message.from_user.id != ADMIN_ID:
        return

    if waiting_id:
        try:
            user_id = int(message.text)

            if is_registered(user_id):
                await message.answer("⚠️ Bu ID allaqachon ro'yxatda.")
                waiting_id = False
            else:
                pending_user_id = user_id
                waiting_id = False
                waiting_name = True
                await message.answer("Endi bu foydalanuvchining ismini yuboring:")

        except ValueError:
            await message.answer("❌ Faqat raqamli ID yuboring")

        return

    if waiting_name:
        name = message.text.strip()
        add_user(pending_user_id, name)

        await message.answer(
            f"✅ Foydalanuvchi qo'shildi\n\n👤 Ism: {name}\n🆔 {pending_user_id}"
        )

        waiting_name = False
        pending_user_id = None
        return

    if waiting_delete_id:
        try:
            user_id = int(message.text)
            deleted = delete_user(user_id)

            if deleted:
                await message.answer(f"🗑 Foydalanuvchi o'chirildi\n\n🆔 {user_id}")
            else:
                await message.answer("⚠️ Bunday ID ro'yxatda topilmadi.")

            waiting_delete_id = False

        except ValueError:
            await message.answer("❌ Faqat raqamli ID yuboring")


async def main():
    create_table()

    # Eski/"osilib qolgan" xabarlarni tozalab yuboradi - bot qayta ishga tushganda
    # avvalgi xabarlarni qayta-qayta qayta ishlab, takrorlanish muammosini oldini oladi
    await bot.delete_webhook(drop_pending_updates=True)

    print("Bot ishga tushdi ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
