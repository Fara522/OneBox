from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from models.user import UserModel
from models.order import OrderModel
from states.customer_states import CustomerOrder
from keyboards.customer_kb import (
    customer_main_menu, skip_comment_keyboard,
    confirm_order_keyboard, back_to_customer,
)
from utils.helpers import format_datetime

router = Router()


async def _customer(telegram_id: int) -> dict | None:
    u = await UserModel.get_by_telegram_id(telegram_id)
    return u if u and u["role"] == "customer" else None


# ─── Back / Cancel ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "customer:back")
async def customer_back(callback: CallbackQuery, state: FSMContext):
    customer = await _customer(callback.from_user.id)
    if not customer:
        return
    await state.clear()
    await callback.message.edit_text(
        f"📋 Salom, <b>{customer['full_name']}</b>!\n\nBuyurtma paneli:",
        reply_markup=customer_main_menu(), parse_mode="HTML"
    )


@router.callback_query(F.data == "customer:cancel")
async def customer_cancel(callback: CallbackQuery, state: FSMContext):
    customer = await _customer(callback.from_user.id)
    if not customer:
        return
    await state.clear()
    await callback.message.edit_text(
        f"📋 Salom, <b>{customer['full_name']}</b>!\n\nBuyurtma paneli:",
        reply_markup=customer_main_menu(), parse_mode="HTML"
    )


# ─── Place order FSM ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "customer:order")
async def customer_order_start(callback: CallbackQuery, state: FSMContext):
    customer = await _customer(callback.from_user.id)
    if not customer:
        return
    await callback.message.edit_text(
        "📦 <b>Yangi buyurtma</b>\n\nMahsulot nomini kiriting:\n"
        "<i>Masalan: Laylo 24x24</i>",
        parse_mode="HTML"
    )
    await state.set_state(CustomerOrder.enter_product)
    await state.update_data(customer_id=customer["id"])


@router.message(CustomerOrder.enter_product)
async def order_enter_product(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Mahsulot nomi juda qisqa. Qayta kiriting:")
        return
    await state.update_data(product_name=name)
    await message.answer("🔢 Sonini kiriting (faqat raqam):")
    await state.set_state(CustomerOrder.enter_quantity)


@router.message(CustomerOrder.enter_quantity)
async def order_enter_quantity(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", "").replace(" ", "")
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Faqat musbat raqam kiriting:")
        return
    await state.update_data(quantity=int(text))
    await message.answer(
        "💬 Izoh yozing yoki o'tkazib yuboring:",
        reply_markup=skip_comment_keyboard()
    )
    await state.set_state(CustomerOrder.enter_comment)


@router.message(CustomerOrder.enter_comment)
async def order_enter_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text.strip())
    data = await state.get_data()
    await message.answer(
        _order_preview(data),
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(CustomerOrder.enter_comment, F.data == "skip_comment")
async def order_skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    data = await state.get_data()
    await callback.message.edit_text(
        _order_preview(data),
        reply_markup=confirm_order_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "send_order")
async def send_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    customer = await _customer(callback.from_user.id)
    if not customer:
        return
    data = await state.get_data()
    if not data.get("customer_id") or not data.get("product_name"):
        await callback.answer("Sessiya tugagan. Qayta boshlang.", show_alert=True)
        await state.clear()
        await callback.message.edit_text(
            f"📋 Salom, <b>{customer['full_name']}</b>!\n\nBuyurtma paneli:",
            reply_markup=customer_main_menu(), parse_mode="HTML"
        )
        return
    await state.clear()

    order_id = await OrderModel.create(
        customer_id=data["customer_id"],
        product_name=data["product_name"],
        quantity=data["quantity"],
        comment=data.get("comment"),
    )

    await callback.message.edit_text(
        f"✅ <b>Buyurtma #{order_id} yuborildi!</b>\n\n"
        f"📦 {data['product_name']} — {data['quantity']:,} ta\n"
        + (f"💬 {data['comment']}\n" if data.get("comment") else "")
        + "\nIshchilar tez orada qabul qilishadi.",
        reply_markup=customer_main_menu(),
        parse_mode="HTML"
    )

    await _broadcast_order(bot, order_id, data, customer["full_name"])


# ─── My orders ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "customer:my_orders")
async def my_orders(callback: CallbackQuery):
    customer = await _customer(callback.from_user.id)
    if not customer:
        return
    orders = await OrderModel.get_by_customer(customer["id"])
    if not orders:
        await callback.message.edit_text(
            "📋 Hali buyurtma yo'q.",
            reply_markup=back_to_customer()
        )
        return
    STATUS = {
        "pending": "🔴 Kutmoqda",
        "in_progress": "🔵 Jarayonda",
        "next_stage": "🟡 Keyingi bosqich",
        "completed": "✅ Tayyor",
        "cancelled": "❌ Bekor",
    }
    lines = [f"📋 <b>Mening buyurtmalarim</b> ({len(orders)} ta):\n"]
    for o in orders:
        comment = f"\n    💬 {o['comment']}" if o.get("comment") else ""
        lines.append(
            f"#{o['id']} {STATUS.get(o['status'], o['status'])}\n"
            f"  📦 {o['product_name']} — {o['quantity']:,} ta{comment}\n"
            f"  🕐 {format_datetime(o['created_at'])}\n"
        )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_customer(),
        parse_mode="HTML"
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _order_preview(data: dict) -> str:
    comment = f"\n💬 Izoh: {data['comment']}" if data.get("comment") else ""
    return (
        f"📦 <b>Buyurtma tasdig'i</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 Mahsulot: <b>{data['product_name']}</b>\n"
        f"🔢 Soni: <b>{data['quantity']:,} ta</b>{comment}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Yuborishni tasdiqlaysizmi?"
    )


async def _broadcast_order(bot: Bot, order_id: int, data: dict, customer_name: str):
    comment = f"\n💬 Izoh: {data['comment']}" if data.get("comment") else ""
    msg = (
        f"🔴 <b>YANGI BUYURTMA #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 Mahsulot: <b>{data['product_name']}</b>\n"
        f"🔢 Soni: <b>{data['quantity']:,} ta</b>{comment}\n"
        f"👤 Buyurtmachi: {customer_name}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    workers = await UserModel.get_all_by_role("worker")
    bosses = await UserModel.get_all_bosses_with_telegram()
    admins = await UserModel.get_all_admins_with_telegram()
    for u in workers + bosses + admins:
        if u.get("telegram_id"):
            try:
                await bot.send_message(u["telegram_id"], msg, parse_mode="HTML")
            except Exception:
                pass
