from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models.user import UserModel
from models.order import OrderModel
from states.boss_states import BossLogin
from states.admin_states import AdminLogin
from states.worker_states import WorkerRegister
from keyboards.worker_kb import (
    start_keyboard, user_names_keyboard,
    worker_main_menu, worker_main_menu_active,
)
from keyboards.boss_kb import boss_main_menu
from keyboards.admin_kb import admin_main_menu
from keyboards.customer_kb import customer_main_menu

router = Router()


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await UserModel.get_by_telegram_id(message.from_user.id)

    if user and user["is_active"]:
        await _show_panel(message, user)
        return

    await message.answer(
        "👋 <b>Xush kelibsiz!</b>\n\nSiz kimchasiz?",
        reply_markup=start_keyboard(),
        parse_mode="HTML",
    )


async def _show_panel(target, user: dict):
    """Show the appropriate panel for a known user."""
    role = user["role"]
    name = user["full_name"]
    send = target.answer if isinstance(target, Message) else target.message.edit_text

    if role == "boss":
        await send(
            f"✅ Xush kelibsiz, <b>{name}</b>!\n🔑 Boss paneli:",
            reply_markup=boss_main_menu(), parse_mode="HTML"
        )
    elif role == "admin":
        await send(
            f"✅ Xush kelibsiz, <b>{name}</b>!\n⚙️ Admin paneli:",
            reply_markup=admin_main_menu(), parse_mode="HTML"
        )
    elif role == "worker":
        active = await OrderModel.get_active_stage(user["id"])
        if active:
            await send(
                f"👷 Salom, <b>{name}</b>!\n\n"
                f"⚠️ Faol buyurtmangiz bor:\n"
                f"📦 {active['product_name']} — {active['quantity']:,} ta\n"
                f"🏭 {active['machine_name']}",
                reply_markup=worker_main_menu_active(), parse_mode="HTML"
            )
        else:
            await send(
                f"👷 Salom, <b>{name}</b>!\n\n📋 Buyurtmalar paneli:",
                reply_markup=worker_main_menu(), parse_mode="HTML"
            )
    elif role == "customer":
        await send(
            f"📋 Salom, <b>{name}</b>!\n\nBuyurtma paneli:",
            reply_markup=customer_main_menu(), parse_mode="HTML"
        )


# ─── Role selection ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "role:boss")
async def role_boss(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔑 <b>Boss kirish</b>\n\nLoginингizni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(BossLogin.waiting_login)


@router.callback_query(F.data == "role:admin")
async def role_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⚙️ <b>Admin kirish</b>\n\nLoginингizni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminLogin.waiting_login)


@router.callback_query(F.data == "role:worker")
async def role_worker(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    workers = await UserModel.get_unlinked_by_role("worker")
    if not workers:
        await callback.message.edit_text(
            "⚠️ Ishchi ro'yxatda yo'q yoki hammasi bog'langan.\n"
            "Admin bilan bog'laning.",
            reply_markup=_back_start_kb()
        )
        return
    await callback.message.edit_text(
        "👷 <b>O'z ismingizni tanlang:</b>",
        reply_markup=user_names_keyboard(workers),
        parse_mode="HTML"
    )
    await state.set_state(WorkerRegister.select_name)
    await state.update_data(reg_role="worker")


@router.callback_query(F.data == "role:customer")
async def role_customer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    customers = await UserModel.get_unlinked_by_role("customer")
    if not customers:
        await callback.message.edit_text(
            "⚠️ Buyurtmachi ro'yxatda yo'q yoki hammasi bog'langan.\n"
            "Boss bilan bog'laning.",
            reply_markup=_back_start_kb()
        )
        return
    await callback.message.edit_text(
        "📋 <b>O'z ismingizni tanlang:</b>",
        reply_markup=user_names_keyboard(customers),
        parse_mode="HTML"
    )
    await state.set_state(WorkerRegister.select_name)
    await state.update_data(reg_role="customer")


# ─── Boss Login FSM ───────────────────────────────────────────────────────────

@router.message(BossLogin.waiting_login)
async def boss_login(message: Message, state: FSMContext):
    user = await UserModel.get_by_login(message.text.strip())
    if not user or user["role"] != "boss":
        await message.answer("❌ Login topilmadi. Qayta kiriting:")
        return
    await state.update_data(auth_user_id=user["id"])
    await message.answer("🔒 Parolni kiriting:")
    await state.set_state(BossLogin.waiting_password)


@router.message(BossLogin.waiting_password)
async def boss_password(message: Message, state: FSMContext):
    from utils.helpers import verify_password
    data = await state.get_data()
    user = await UserModel.get_by_id(data["auth_user_id"])
    if not verify_password(message.text, user["password_hash"] or ""):
        await message.answer("❌ Parol noto'g'ri. Qayta kiriting:")
        return
    await UserModel.link_telegram(user["id"], message.from_user.id, message.from_user.username)
    await state.clear()
    await message.answer(
        f"✅ Xush kelibsiz, <b>{user['full_name']}</b>!\n🔑 Boss paneli:",
        reply_markup=boss_main_menu(), parse_mode="HTML"
    )


# ─── Admin Login FSM ──────────────────────────────────────────────────────────

@router.message(AdminLogin.waiting_login)
async def admin_login(message: Message, state: FSMContext):
    user = await UserModel.get_by_login(message.text.strip())
    if not user or user["role"] != "admin":
        await message.answer("❌ Login topilmadi. Qayta kiriting:")
        return
    await state.update_data(auth_user_id=user["id"])
    await message.answer("🔒 Parolni kiriting:")
    await state.set_state(AdminLogin.waiting_password)


@router.message(AdminLogin.waiting_password)
async def admin_password(message: Message, state: FSMContext):
    from utils.helpers import verify_password
    data = await state.get_data()
    user = await UserModel.get_by_id(data["auth_user_id"])
    if not verify_password(message.text, user["password_hash"] or ""):
        await message.answer("❌ Parol noto'g'ri. Qayta kiriting:")
        return
    await UserModel.link_telegram(user["id"], message.from_user.id, message.from_user.username)
    await state.clear()
    await message.answer(
        f"✅ Xush kelibsiz, <b>{user['full_name']}</b>!\n⚙️ Admin paneli:",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Name selection (worker / customer) ──────────────────────────────────────

@router.callback_query(F.data.startswith("select_name:"))
async def name_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = int(callback.data.split(":")[1])
    user = await UserModel.get_by_id(user_id)
    if not user:
        await callback.answer("Xatolik.", show_alert=True)
        return
    if user["telegram_id"] is not None:
        await callback.answer("Bu ism allaqachon band.", show_alert=True)
        return
    await UserModel.link_telegram(user_id, callback.from_user.id, callback.from_user.username)
    await state.clear()
    await _show_panel(callback, user)


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "logout")
async def logout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await UserModel.logout(callback.from_user.id)
    await callback.message.edit_text(
        "🚪 Chiqildi.\n\n👋 Qayta kirish uchun /start bosing."
    )


# ─── Back to start ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Xush kelibsiz!</b>\n\nSiz kimchasiz?",
        reply_markup=start_keyboard(), parse_mode="HTML"
    )


def _back_start_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Orqaga", callback_data="back_to_start")
    return b.as_markup()
