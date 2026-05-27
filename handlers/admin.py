from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models.user import UserModel
from models.machine import MachineModel
from models.assignment import AssignmentModel
from models.order import OrderModel
from states.admin_states import (
    AdminAddWorker, AdminAddMachine,
    AdminAssignMachine, AdminDeleteWorker, AdminEditWorker, AdminDeleteMachine,
)
from keyboards.admin_kb import (
    admin_main_menu, workers_keyboard, machines_keyboard,
    confirm_delete_keyboard, confirm_delete_machine_keyboard,
    edit_field_keyboard, back_to_admin, orders_nav_keyboard,
)
from utils.helpers import format_datetime

router = Router()
PAGE_SIZE = 10


async def _admin(telegram_id: int) -> dict | None:
    u = await UserModel.get_by_telegram_id(telegram_id)
    return u if u and u["role"] in ("admin", "boss") else None


@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("⚙️ Admin paneli:", reply_markup=admin_main_menu())


# ─── Add Worker ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:add_worker")
async def add_worker_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    await callback.message.edit_text("👤 Yangi ishchi to'liq ismini kiriting:")
    await state.set_state(AdminAddWorker.full_name)


@router.message(AdminAddWorker.full_name)
async def add_worker_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Ism juda qisqa:")
        return
    await state.update_data(worker_name=name)
    await message.answer("🎂 Yoshini kiriting (faqat raqam, masalan: 25):")
    await state.set_state(AdminAddWorker.age)


@router.message(AdminAddWorker.age)
async def add_worker_age(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (14 <= int(text) <= 80):
        await message.answer("⚠️ Yosh 14 dan 80 gacha bo'lishi kerak:")
        return
    data = await state.get_data()
    wid = await UserModel.create_worker(data["worker_name"], int(text))
    await state.clear()
    await message.answer(
        f"✅ Ishchi qo'shildi: <b>{data['worker_name']}</b>, {text} yosh (ID: {wid})\n\n"
        "Ishchi /start orqali o'z ismini tanlab kiradi.",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Remove Worker ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:remove_worker")
async def remove_worker_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    workers = await UserModel.get_all_by_role("worker")
    if not workers:
        await callback.message.edit_text("⚠️ Ishchi yo'q.", reply_markup=back_to_admin())
        return
    await callback.message.edit_text(
        "❌ Qaysi ishchini o'chirmoqchisiz?",
        reply_markup=workers_keyboard(workers, "pre_delete"),
    )
    await state.set_state(AdminDeleteWorker.confirm)


@router.callback_query(AdminDeleteWorker.confirm, F.data.startswith("pre_delete:"))
async def pre_delete(callback: CallbackQuery, state: FSMContext):
    wid = int(callback.data.split(":")[1])
    w = await UserModel.get_by_id(wid)
    if not w:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    await state.update_data(del_id=wid)
    await callback.message.edit_text(
        f"⚠️ <b>{w['full_name']}</b>ni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_keyboard(wid), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    wid = int(callback.data.split(":")[1])
    w = await UserModel.get_by_id(wid)
    await AssignmentModel.remove_worker(wid)
    await UserModel.deactivate(wid)
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>{w['full_name']}</b> o'chirildi.",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Add Machine ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:add_machine")
async def add_machine_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    await callback.message.edit_text("🏭 Yangi stanok nomini kiriting:")
    await state.set_state(AdminAddMachine.name)


@router.message(AdminAddMachine.name)
async def add_machine_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Nom qisqa:")
        return
    await state.update_data(machine_name=name)
    await message.answer("📝 Tavsif kiriting (yoki « - » yozing):")
    await state.set_state(AdminAddMachine.description)


@router.message(AdminAddMachine.description)
async def add_machine_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    desc = None if message.text.strip() == "-" else message.text.strip()
    mid = await MachineModel.create(data["machine_name"], desc)
    await state.clear()
    await message.answer(
        f"✅ Stanok qo'shildi: <b>{data['machine_name']}</b> (ID: {mid})",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Remove Machine ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:remove_machine")
async def remove_machine_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    machines = await MachineModel.get_all_active()
    if not machines:
        await callback.message.edit_text("⚠️ Stanok yo'q.", reply_markup=back_to_admin())
        return
    await callback.message.edit_text(
        "❌ Qaysi stanokni o'chirmoqchisiz?",
        reply_markup=machines_keyboard(machines, "pre_delete_machine"),
    )
    await state.set_state(AdminDeleteMachine.confirm)


@router.callback_query(AdminDeleteMachine.confirm, F.data.startswith("pre_delete_machine:"))
async def pre_delete_machine(callback: CallbackQuery, state: FSMContext):
    mid = int(callback.data.split(":")[1])
    m = await MachineModel.get_by_id(mid)
    if not m:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    await state.update_data(del_machine_id=mid)
    await callback.message.edit_text(
        f"⚠️ <b>{m['name']}</b> stanokini o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_delete_machine_keyboard(mid), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_delete_machine:"))
async def confirm_delete_machine(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    mid = int(callback.data.split(":")[1])
    m = await MachineModel.get_by_id(mid)
    await MachineModel.deactivate(mid)
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>{m['name']}</b> stanoki o'chirildi.",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Assign Machine ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:assign_machine")
async def assign_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    workers = await UserModel.get_all_by_role("worker")
    if not workers:
        await callback.message.edit_text("⚠️ Ishchi yo'q.", reply_markup=back_to_admin())
        return
    await callback.message.edit_text(
        "🔗 Qaysi ishchiga stanok biriktirasiz?",
        reply_markup=workers_keyboard(workers, "assign_worker"),
    )
    await state.set_state(AdminAssignMachine.select_worker)


@router.callback_query(AdminAssignMachine.select_worker, F.data.startswith("assign_worker:"))
async def assign_select_worker(callback: CallbackQuery, state: FSMContext):
    wid = int(callback.data.split(":")[1])
    await state.update_data(assign_wid=wid)
    machines = await MachineModel.get_all_active()
    if not machines:
        await callback.message.edit_text("⚠️ Stanok yo'q.", reply_markup=back_to_admin())
        return
    await callback.message.edit_text(
        "🏭 Qaysi stanokni biriktirasiz?",
        reply_markup=machines_keyboard(machines, "assign_machine"),
    )
    await state.set_state(AdminAssignMachine.select_machine)


@router.callback_query(AdminAssignMachine.select_machine, F.data.startswith("assign_machine:"))
async def assign_select_machine(callback: CallbackQuery, state: FSMContext):
    mid = int(callback.data.split(":")[1])
    data = await state.get_data()
    w = await UserModel.get_by_id(data["assign_wid"])
    m = await MachineModel.get_by_id(mid)
    await AssignmentModel.create(mid, data["assign_wid"])
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>{w['full_name']}</b> → <b>{m['name']}</b> biriktirildi.",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Edit Worker ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:edit_worker")
async def edit_worker_start(callback: CallbackQuery, state: FSMContext):
    if not await _admin(callback.from_user.id):
        return
    workers = await UserModel.get_all_by_role("worker")
    if not workers:
        await callback.message.edit_text("⚠️ Ishchi yo'q.", reply_markup=back_to_admin())
        return
    await callback.message.edit_text(
        "✏️ Qaysi ishchini tahrirlaysiz?",
        reply_markup=workers_keyboard(workers, "edit_select_worker"),
    )
    await state.set_state(AdminEditWorker.select_worker)


@router.callback_query(AdminEditWorker.select_worker, F.data.startswith("edit_select_worker:"))
async def edit_select_worker(callback: CallbackQuery, state: FSMContext):
    wid = int(callback.data.split(":")[1])
    w = await UserModel.get_by_id(wid)
    await state.update_data(edit_wid=wid)
    await callback.message.edit_text(
        f"✏️ <b>{w['full_name']}</b>\n\nNimani o'zgartirish?",
        reply_markup=edit_field_keyboard(wid), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("edit_name:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    wid = int(callback.data.split(":")[1])
    await state.update_data(edit_wid=wid)
    await callback.message.edit_text("👤 Yangi ismni kiriting:")
    await state.set_state(AdminEditWorker.new_value)


@router.message(AdminEditWorker.new_value)
async def edit_name_done(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Ism qisqa:")
        return
    data = await state.get_data()
    await UserModel.update_full_name(data["edit_wid"], name)
    await state.clear()
    await message.answer(
        f"✅ Ism o'zgartirildi: <b>{name}</b>",
        reply_markup=admin_main_menu(), parse_mode="HTML"
    )


# ─── Orders ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:orders:"))
async def admin_orders(callback: CallbackQuery):
    if not await _admin(callback.from_user.id):
        return
    offset = int(callback.data.split(":")[2])
    orders = await OrderModel.get_all(limit=PAGE_SIZE, offset=offset)
    total = await OrderModel.count_all()
    if not orders:
        await callback.message.edit_text("📋 Buyurtma yo'q.", reply_markup=back_to_admin())
        return
    STATUS = {"pending": "🔴", "in_progress": "🔵", "next_stage": "🟡",
              "completed": "✅", "cancelled": "❌"}
    lines = [f"📋 <b>Buyurtmalar</b> ({offset+1}–{offset+len(orders)} / {total}):\n"]
    for o in orders:
        lines.append(
            f"{STATUS.get(o['status'], '?')} #{o['id']} <b>{o['product_name']}</b> "
            f"— {o['quantity']:,} ta\n"
            f"  👤 {o['customer_name']}  🕐 {format_datetime(o['created_at'])}\n"
        )
    has_more = (offset + PAGE_SIZE) < total
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=orders_nav_keyboard(offset, has_more), parse_mode="HTML"
    )
