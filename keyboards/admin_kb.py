from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Ishchi qo'shish", callback_data="admin:add_worker")
    builder.button(text="❌ Ishchini o'chirish", callback_data="admin:remove_worker")
    builder.button(text="🏭 Stanok qo'shish", callback_data="admin:add_machine")
    builder.button(text="❌ Stanokni o'chirish", callback_data="admin:remove_machine")
    builder.button(text="🔗 Stanok biriktirish", callback_data="admin:assign_machine")
    builder.button(text="✏️ Ishchini tahrirlash", callback_data="admin:edit_worker")
    builder.button(text="📋 Buyurtmalar", callback_data="admin:orders:0")
    builder.button(text="🚪 Chiqish", callback_data="logout")
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup()


def workers_keyboard(workers: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for w in workers:
        builder.button(text=f"👷 {w['full_name']}", callback_data=f"{action_prefix}:{w['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def machines_keyboard(machines: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in machines:
        builder.button(text=f"🏭 {m['name']}", callback_data=f"{action_prefix}:{m['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_keyboard(worker_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"confirm_delete:{worker_id}")
    builder.button(text="❌ Bekor qilish", callback_data="admin:back")
    builder.adjust(2)
    return builder.as_markup()


def edit_field_keyboard(worker_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Ismini o'zgartirish", callback_data=f"edit_name:{worker_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_machine_keyboard(machine_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_machine:{machine_id}")
    builder.button(text="❌ Bekor qilish", callback_data="admin:back")
    builder.adjust(2)
    return builder.as_markup()


def back_to_admin() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Asosiy menyu", callback_data="admin:back")
    builder.adjust(1)
    return builder.as_markup()


def orders_nav_keyboard(offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if offset > 0:
        builder.button(text="◀️ Oldingi", callback_data=f"admin:orders:{offset - 10}")
    if has_more:
        builder.button(text="Keyingi ▶️", callback_data=f"admin:orders:{offset + 10}")
    builder.button(text="⬅️ Asosiy menyu", callback_data="admin:back")
    builder.adjust(2, 1)
    return builder.as_markup()


# backward compat
def reports_nav_keyboard(offset: int, has_more: bool) -> InlineKeyboardMarkup:
    return orders_nav_keyboard(offset, has_more)
