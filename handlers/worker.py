from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models.user import UserModel
from models.machine import MachineModel
from models.order import OrderModel
from states.worker_states import WorkerStartOrder
from keyboards.worker_kb import (
    worker_main_menu, worker_main_menu_active,
    orders_list_keyboard, order_machine_keyboard,
    working_order_keyboard, confirm_finish_keyboard,
    skip_helper_keyboard,
)
from utils.helpers import format_datetime

router = Router()


async def _worker(telegram_id: int) -> dict | None:
    u = await UserModel.get_by_telegram_id(telegram_id)
    return u if u and u["role"] == "worker" else None


def _order_card(order: dict) -> str:
    STATUS = {
        "pending": "🔴 Yangi buyurtma",
        "next_stage": "🟡 Keyingi bosqich",
        "in_progress": "🔵 Jarayonda",
    }
    comment = f"\n💬 Izoh: {order['comment']}" if order.get("comment") else ""
    return (
        f"📦 <b>BUYURTMA #{order['id']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 Mahsulot: <b>{order['product_name']}</b>\n"
        f"🔢 Soni: <b>{order['quantity']:,} ta</b>{comment}\n"
        f"👤 Buyurtmachi: {order['customer_name']}\n"
        f"🕐 Vaqt: {format_datetime(order['created_at'])}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{STATUS.get(order['status'], order['status'])}"
    )


# ─── Worker main menu ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "worker:back")
async def worker_back(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    await state.clear()
    active = await OrderModel.get_active_stage(worker["id"])
    menu = worker_main_menu_active() if active else worker_main_menu()
    await callback.message.edit_text(
        f"👷 <b>{worker['full_name']}</b>\n📋 Buyurtmalar paneli:",
        reply_markup=menu, parse_mode="HTML"
    )


@router.callback_query(F.data == "worker:active")
async def worker_active(callback: CallbackQuery):
    await callback.answer()
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    stage = await OrderModel.get_active_stage(worker["id"])
    if not stage:
        await callback.message.edit_text(
            "⚠️ Faol ish topilmadi.", reply_markup=worker_main_menu()
        )
        return
    helper_line = f"\n👥 Yordamchi: {stage['helper_name']}" if stage.get("helper_name") else ""
    await callback.message.edit_text(
        f"▶️ <b>Faol ish</b>\n\n"
        f"📦 {stage['product_name']} — {stage['quantity']:,} ta\n"
        f"🏭 Stanok: {stage['machine_name']}{helper_line}\n"
        f"💬 Izoh: {stage.get('comment') or '—'}\n"
        f"🕐 Boshlangan: {format_datetime(stage['start_time'])}\n\n"
        "Ish tugaganda quyidagi tugmalardan birini bosing:",
        reply_markup=working_order_keyboard(stage["id"]),
        parse_mode="HTML"
    )


# ─── Orders list ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "worker:orders")
async def worker_orders(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    await state.clear()
    active = await OrderModel.get_active_stage(worker["id"])
    if active:
        helper_line = f"\n👥 Yordamchi: {active['helper_name']}" if active.get("helper_name") else ""
        try:
            await callback.message.edit_text(
                f"⚠️ <b>Faol ishingiz bor!</b>\n\n"
                f"📦 {active['product_name']} — {active['quantity']:,} ta\n"
                f"🏭 Stanok: {active['machine_name']}{helper_line}\n\n"
                "Avval uni tugatish yoki keyingi bosqichga o'tkazing:",
                reply_markup=working_order_keyboard(active["id"]),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return
    orders = await OrderModel.get_pending()
    if not orders:
        try:
            await callback.message.edit_text(
                "📋 Hozircha yangi buyurtma yo'q.\n\n"
                "Buyurtmachi buyurtma yuborganida xabar olasiz.",
                reply_markup=worker_main_menu()
            )
        except Exception:
            pass
        return
    try:
        await callback.message.edit_text(
            "📋 <b>Kutilayotgan buyurtmalar:</b>",
            reply_markup=orders_list_keyboard(orders),
            parse_mode="HTML"
        )
    except Exception:
        pass


# ─── Accept order ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("accept_order:"))
async def accept_order(callback: CallbackQuery):
    await callback.answer()
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    order_id = int(callback.data.split(":")[1])
    order = await OrderModel.get_by_id(order_id)
    if not order or order["status"] not in ("pending", "next_stage"):
        await callback.answer("Bu buyurtma allaqachon qabul qilingan!", show_alert=True)
        return
    machines = await MachineModel.get_all_active()
    if not machines:
        await callback.answer("Stanok yo'q!", show_alert=True)
        return
    await callback.message.edit_text(
        _order_card(order) + "\n\n🏭 Qaysi stanokda ishlaysiz?",
        reply_markup=order_machine_keyboard(machines, order_id),
        parse_mode="HTML"
    )


# ─── Select machine → ask helper ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("select_machine:"))
async def select_machine(callback: CallbackQuery, state: FSMContext):
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    parts = callback.data.split(":")
    order_id, machine_id = int(parts[1]), int(parts[2])
    order = await OrderModel.get_by_id(order_id)
    if not order or order["status"] not in ("pending", "next_stage"):
        await callback.answer("Bu buyurtma allaqachon band!", show_alert=True)
        return
    machine = await MachineModel.get_by_id(machine_id)
    await state.set_state(WorkerStartOrder.enter_helper)
    await state.update_data(pending_order_id=order_id, pending_machine_id=machine_id)
    await callback.message.edit_text(
        f"🏭 Stanok: <b>{machine['name']}</b>\n\n"
        f"👥 Yordamchi ismini kiriting yoki o'tkazib yuboring:",
        reply_markup=skip_helper_keyboard(),
        parse_mode="HTML"
    )


@router.message(WorkerStartOrder.enter_helper)
async def enter_helper(message: Message, state: FSMContext, bot: Bot):
    worker = await _worker(message.from_user.id)
    if not worker:
        return
    helper_name = message.text.strip() or None
    await _do_start_order(message, state, bot, worker, helper_name)


@router.callback_query(WorkerStartOrder.enter_helper, F.data == "skip_helper")
async def skip_helper(callback: CallbackQuery, state: FSMContext, bot: Bot):
    worker = await _worker(callback.from_user.id)
    if not worker:
        return
    await _do_start_order(callback, state, bot, worker, None)


async def _do_start_order(target, state: FSMContext, bot: Bot, worker: dict, helper_name: str | None):
    data = await state.get_data()
    order_id = data["pending_order_id"]
    machine_id = data["pending_machine_id"]
    await state.clear()

    order = await OrderModel.get_by_id(order_id)
    if not order or order["status"] not in ("pending", "next_stage"):
        send = target.answer if isinstance(target, Message) else target.message.edit_text
        await send("⚠️ Bu buyurtma allaqachon band!")
        return

    stage_num = await OrderModel.get_stage_count(order_id) + 1
    stage_id = await OrderModel.create_stage(order_id, worker["id"], machine_id, stage_num, helper_name)
    await OrderModel.set_status(order_id, "in_progress")

    machine = await MachineModel.get_by_id(machine_id)
    helper_line = f"\n👥 Yordamchi: {helper_name}" if helper_name else ""
    text = (
        f"▶️ <b>Ish boshlandi!</b>\n\n"
        f"📦 {order['product_name']} — {order['quantity']:,} ta\n"
        f"🏭 Stanok: {machine['name']}{helper_line}\n"
        f"💬 Izoh: {order.get('comment') or '—'}\n\n"
        "Tugatgach quyidagi tugmalardan birini bosing:"
    )
    kb = working_order_keyboard(stage_id)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

    await _notify_staff(
        bot,
        f"🔵 <b>Buyurtma #{order_id} boshlandi</b>\n"
        f"👷 Ishchi: {worker['full_name']}\n"
        f"🏭 Stanok: {machine['name']}\n"
        + (f"👥 Yordamchi: {helper_name}\n" if helper_name else "")
        + f"📦 {order['product_name']} — {order['quantity']:,} ta",
        exclude=target.from_user.id if isinstance(target, Message) else target.from_user.id
    )


# ─── Finish / Next stage ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("done_order:"))
async def done_order(callback: CallbackQuery):
    stage_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "⚠️ Buyurtmani tugatish haqida qaror qabul qiling:",
        reply_markup=confirm_finish_keyboard(stage_id)
    )


@router.callback_query(F.data.startswith("next_stage:"))
async def next_stage_confirm(callback: CallbackQuery):
    stage_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "⚠️ Keyingi bosqichga o'tkazish haqida qaror qabul qiling:",
        reply_markup=confirm_finish_keyboard(stage_id)
    )


@router.callback_query(F.data.startswith("confirm_done:"))
async def confirm_done(callback: CallbackQuery, bot: Bot):
    stage_id = int(callback.data.split(":")[1])
    stage = await OrderModel.complete_stage(stage_id)
    if not stage:
        await callback.answer("Xatolik.", show_alert=True)
        return

    order_id = stage["order_id"]
    await OrderModel.set_status(order_id, "completed")

    await callback.message.edit_text(
        f"✅ <b>Buyurtma #{order_id} yakunlandi!</b>\n\n"
        f"📦 {stage['product_name']} — {stage['quantity']:,} ta\n"
        f"🏭 Stanok: {stage['machine_name']}\n"
        f"👷 Ishchi: {stage['worker_name']}",
        reply_markup=worker_main_menu(),
        parse_mode="HTML"
    )

    # Notify customer
    if stage.get("customer_tg"):
        try:
            await bot.send_message(
                stage["customer_tg"],
                f"✅ <b>Buyurtmangiz tayyor!</b>\n\n"
                f"📦 {stage['product_name']} — {stage['quantity']:,} ta\n"
                f"🏭 Yakunlagan stanok: {stage['machine_name']}\n"
                f"👷 Ishchi: {stage['worker_name']}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await _notify_staff(
        bot,
        f"✅ <b>Buyurtma #{order_id} YAKUNLANDI</b>\n"
        f"📦 {stage['product_name']} — {stage['quantity']:,} ta\n"
        f"👤 Buyurtmachi: {stage['customer_name']}",
        exclude=callback.from_user.id
    )


@router.callback_query(F.data.startswith("confirm_next:"))
async def confirm_next(callback: CallbackQuery, bot: Bot):
    stage_id = int(callback.data.split(":")[1])
    row = await OrderModel.pass_stage(stage_id)
    if not row:
        await callback.answer("Xatolik.", show_alert=True)
        return

    order_id = row["order_id"]
    order = await OrderModel.get_by_id(order_id)
    await OrderModel.set_status(order_id, "next_stage")

    await callback.message.edit_text(
        f"⏭ <b>Buyurtma #{order_id} keyingi bosqichga o'tkazildi!</b>\n\n"
        f"📦 {order['product_name']} — {order['quantity']:,} ta\n\n"
        "Boshqa ishchi qabul qilishi mumkin.",
        reply_markup=worker_main_menu(),
        parse_mode="HTML"
    )

    # Broadcast pending to all workers
    workers = await UserModel.get_all_admins_with_telegram()
    all_workers = await UserModel.get_all_by_role("worker")
    recipients = workers + all_workers
    comment = f"\n💬 Izoh: {order['comment']}" if order.get("comment") else ""
    msg = (
        f"🟡 <b>BUYURTMA #{order_id} — KEYINGI BOSQICH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 Mahsulot: <b>{order['product_name']}</b>\n"
        f"🔢 Soni: <b>{order['quantity']:,} ta</b>{comment}\n"
        f"👤 Buyurtmachi: {order['customer_name']}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    for r in recipients:
        if r.get("telegram_id") and r["telegram_id"] != callback.from_user.id:
            try:
                await bot.send_message(r["telegram_id"], msg, parse_mode="HTML")
            except Exception:
                pass


async def _notify_staff(bot: Bot, text: str, exclude: int = 0):
    bosses = await UserModel.get_all_bosses_with_telegram()
    admins = await UserModel.get_all_admins_with_telegram()
    for u in bosses + admins:
        if u.get("telegram_id") and u["telegram_id"] != exclude:
            try:
                await bot.send_message(u["telegram_id"], text, parse_mode="HTML")
            except Exception:
                pass
