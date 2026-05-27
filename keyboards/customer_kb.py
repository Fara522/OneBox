from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def customer_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Buyurtma berish", callback_data="customer:order")
    builder.button(text="📋 Mening buyurtmalarim", callback_data="customer:my_orders")
    builder.button(text="🚪 Chiqish", callback_data="logout")
    builder.adjust(1)
    return builder.as_markup()


def skip_comment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Izohsiz yuborish", callback_data="skip_comment")
    builder.button(text="❌ Bekor qilish", callback_data="customer:cancel")
    builder.adjust(1)
    return builder.as_markup()


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Buyurtma berish", callback_data="send_order")
    builder.button(text="❌ Bekor qilish", callback_data="customer:cancel")
    builder.adjust(2)
    return builder.as_markup()


def back_to_customer() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="customer:back")
    builder.adjust(1)
    return builder.as_markup()
