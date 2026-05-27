from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models.user import UserModel
from models.machine import MachineModel
from models.order import OrderModel
from states.boss_states import BossAddAdmin, BossAddCustomer
from keyboards.boss_kb import (
    boss_main_menu, stats_period_keyboard, orders_nav_keyboard, back_to_boss,
    users_list_keyboard, confirm_delete_user_keyboard,
)
from utils.helpers import hash_password, format_datetime
from utils.report_generator import build_stats_text
from models.report import ReportModel

router = Router()
PAGE_SIZE = 10


async def _boss(telegram_id: int) -> dict | None:
    u = await UserModel.get_by_telegram_id(telegram_id)
    return u if u and u["role"] == "boss" else None


@router.callback_query(F.data == "boss:back")
async def boss_back(callback: CallbackQuery, state: FSMContext):
    if not await _boss(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("🔑 Boss paneli:", reply_markup=boss_main_menu())


# ─── Lists ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:workers")
async def boss_workers(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    workers = await UserModel.get_workers_with_machine()
    if not workers:
        await callback.message.edit_text("👷 Ishchi yo'q.", reply_markup=back_to_boss())
        return
    lines = ["👷 <b>Ishchilar:</b>\n"]
    for i, w in enumerate(workers, 1):
        icon = "🟢" if w["telegram_id"] else "🔴"
        age = f", {w['age']} yosh" if w.get("age") else ""
        machine = f" | 🏭 {w['machine_name']}" if w.get("machine_name") else " | 🏭 —"
        lines.append(f"{i}. {icon} {w['full_name']}{age}{machine}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_boss(), parse_mode="HTML")


@router.callback_query(F.data == "boss:admins")
async def boss_admins(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    admins = await UserModel.get_all_by_role("admin")
    if not admins:
        await callback.message.edit_text("👔 Admin yo'q.", reply_markup=back_to_boss())
        return
    lines = ["👔 <b>Adminlar:</b>\n"]
    for i, a in enumerate(admins, 1):
        icon = "🟢" if a["telegram_id"] else "🔴"
        lines.append(f"{i}. {icon} {a['full_name']} (login: <code>{a['login']}</code>)")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_boss(), parse_mode="HTML")


@router.callback_query(F.data == "boss:customers")
async def boss_customers(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    customers = await UserModel.get_all_by_role("customer")
    if not customers:
        await callback.message.edit_text("📋 Buyurtmachi yo'q.", reply_markup=back_to_boss())
        return
    lines = ["📋 <b>Buyurtmachilar:</b>\n"]
    for i, c in enumerate(customers, 1):
        icon = "🟢" if c["telegram_id"] else "🔴"
        lines.append(f"{i}. {icon} {c['full_name']}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_boss(), parse_mode="HTML")


@router.callback_query(F.data == "boss:machines")
async def boss_machines(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    machines = await MachineModel.get_all_active()
    if not machines:
        await callback.message.edit_text("🏭 Stanok yo'q.", reply_markup=back_to_boss())
        return
    lines = ["🏭 <b>Stanoklar:</b>\n"]
    for i, m in enumerate(machines, 1):
        desc = f" — {m['description']}" if m.get("description") else ""
        lines.append(f"{i}. {m['name']}{desc}")
    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_boss(), parse_mode="HTML")


# ─── Orders list ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("boss:orders:"))
async def boss_orders(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    offset = int(callback.data.split(":")[2])
    orders = await OrderModel.get_all(limit=PAGE_SIZE, offset=offset)
    total = await OrderModel.count_all()
    if not orders:
        await callback.message.edit_text("📊 Buyurtma yo'q.", reply_markup=back_to_boss())
        return
    STATUS = {"pending": "🔴 Kutmoqda", "in_progress": "🔵 Jarayonda",
              "next_stage": "🟡 Keyingi", "completed": "✅ Tugadi", "cancelled": "❌ Bekor"}
    lines = [f"📊 <b>Buyurtmalar</b> ({offset+1}–{offset+len(orders)} / {total}):\n"]
    for o in orders:
        lines.append(
            f"#{o['id']} {STATUS.get(o['status'], o['status'])}\n"
            f"  📦 {o['product_name']} — {o['quantity']:,} ta\n"
            f"  👤 {o['customer_name']}  🕐 {format_datetime(o['created_at'])}\n"
        )
    has_more = (offset + PAGE_SIZE) < total
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=orders_nav_keyboard(offset, has_more), parse_mode="HTML"
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:stats")
async def boss_stats(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    await callback.message.edit_text("📈 Davr tanlang:", reply_markup=stats_period_keyboard())


@router.callback_query(F.data.startswith("stats:"))
async def stats_period(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    period = callback.data.split(":")[1]
    data = await ReportModel.get_stats(period)
    await callback.message.edit_text(build_stats_text(data), reply_markup=back_to_boss())


# ─── Add Admin ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if not await _boss(callback.from_user.id):
        return
    await callback.message.edit_text("👔 Yangi admin to'liq ismini kiriting:")
    await state.set_state(BossAddAdmin.full_name)


@router.message(BossAddAdmin.full_name)
async def add_admin_name(message: Message, state: FSMContext):
    await state.update_data(admin_name=message.text.strip())
    await message.answer("🔑 Admin uchun login kiriting:")
    await state.set_state(BossAddAdmin.login)


@router.message(BossAddAdmin.login)
async def add_admin_login(message: Message, state: FSMContext):
    login = message.text.strip()
    if await UserModel.login_exists(login):
        await message.answer("⚠️ Bu login band. Boshqa login kiriting:")
        return
    await state.update_data(admin_login=login)
    await message.answer("🔒 Parol kiriting:")
    await state.set_state(BossAddAdmin.password)


@router.message(BossAddAdmin.password)
async def add_admin_password(message: Message, state: FSMContext):
    data = await state.get_data()
    pw_hash = hash_password(message.text.strip())
    await UserModel.create_staff(data["admin_name"], "admin", data["admin_login"], pw_hash)
    await state.clear()
    await message.answer(
        f"✅ Admin qo'shildi!\n"
        f"👤 Ism: <b>{data['admin_name']}</b>\n"
        f"🔑 Login: <code>{data['admin_login']}</code>\n"
        f"🔒 Parol: <code>{message.text.strip()}</code>",
        reply_markup=boss_main_menu(), parse_mode="HTML"
    )


# ─── Add Customer ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:add_customer")
async def add_customer_start(callback: CallbackQuery, state: FSMContext):
    if not await _boss(callback.from_user.id):
        return
    await callback.message.edit_text("📋 Yangi buyurtmachi to'liq ismini kiriting:")
    await state.set_state(BossAddCustomer.full_name)


@router.message(BossAddCustomer.full_name)
async def add_customer_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await UserModel.create_customer(name)
    await state.clear()
    await message.answer(
        f"✅ Buyurtmachi qo'shildi: <b>{name}</b>\n\n"
        "Endi u /start orqali o'z ismini tanlab botga kira oladi.",
        reply_markup=boss_main_menu(), parse_mode="HTML"
    )


# ─── Remove Admin ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext):
    if not await _boss(callback.from_user.id):
        return
    await state.clear()
    admins = await UserModel.get_all_by_role("admin")
    if not admins:
        await callback.message.edit_text("👔 Admin yo'q.", reply_markup=back_to_boss())
        return
    await callback.message.edit_text(
        "❌ Qaysi adminni o'chirmoqchisiz?",
        reply_markup=users_list_keyboard(admins, "boss_pre_del_admin"),
    )


@router.callback_query(F.data.startswith("boss_pre_del_admin:"))
async def boss_pre_del_admin(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    uid = int(callback.data.split(":")[1])
    u = await UserModel.get_by_id(uid)
    if not u:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    await callback.message.edit_text(
        f"⚠️ <b>{u['full_name']}</b> (login: <code>{u['login']}</code>) adminni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_user_keyboard(uid, "boss_conf_del_admin"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("boss_conf_del_admin:"))
async def boss_conf_del_admin(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    uid = int(callback.data.split(":")[1])
    u = await UserModel.get_by_id(uid)
    await UserModel.deactivate(uid)
    await callback.message.edit_text(
        f"✅ Admin <b>{u['full_name']}</b> o'chirildi.",
        reply_markup=boss_main_menu(), parse_mode="HTML"
    )


# ─── Remove Customer ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "boss:remove_customer")
async def remove_customer_start(callback: CallbackQuery, state: FSMContext):
    if not await _boss(callback.from_user.id):
        return
    await state.clear()
    customers = await UserModel.get_all_by_role("customer")
    if not customers:
        await callback.message.edit_text("📋 Buyurtmachi yo'q.", reply_markup=back_to_boss())
        return
    await callback.message.edit_text(
        "❌ Qaysi buyurtmachini o'chirmoqchisiz?",
        reply_markup=users_list_keyboard(customers, "boss_pre_del_customer"),
    )


@router.callback_query(F.data.startswith("boss_pre_del_customer:"))
async def boss_pre_del_customer(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    uid = int(callback.data.split(":")[1])
    u = await UserModel.get_by_id(uid)
    if not u:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    await callback.message.edit_text(
        f"⚠️ <b>{u['full_name']}</b> buyurtmachini o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_user_keyboard(uid, "boss_conf_del_customer"),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("boss_conf_del_customer:"))
async def boss_conf_del_customer(callback: CallbackQuery):
    if not await _boss(callback.from_user.id):
        return
    uid = int(callback.data.split(":")[1])
    u = await UserModel.get_by_id(uid)
    await UserModel.deactivate(uid)
    await callback.message.edit_text(
        f"✅ Buyurtmachi <b>{u['full_name']}</b> o'chirildi.",
        reply_markup=boss_main_menu(), parse_mode="HTML"
    )
