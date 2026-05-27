from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def boss_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👷 Ishchilar", callback_data="boss:workers")
    builder.button(text="👔 Adminlar", callback_data="boss:admins")
    builder.button(text="📋 Buyurtmachilar", callback_data="boss:customers")
    builder.button(text="🏭 Stanoklar", callback_data="boss:machines")
    builder.button(text="📊 Buyurtmalar", callback_data="boss:orders:0")
    builder.button(text="📈 Statistika", callback_data="boss:stats")
    builder.button(text="➕ Admin qo'shish", callback_data="boss:add_admin")
    builder.button(text="❌ Admin o'chirish", callback_data="boss:remove_admin")
    builder.button(text="➕ Buyurtmachi qo'shish", callback_data="boss:add_customer")
    builder.button(text="❌ Buyurtmachi o'chirish", callback_data="boss:remove_customer")
    builder.button(text="🚪 Chiqish", callback_data="logout")
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()


def stats_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Bugungi", callback_data="stats:daily")
    builder.button(text="📅 Haftalik", callback_data="stats:weekly")
    builder.button(text="📅 Oylik", callback_data="stats:monthly")
    builder.button(text="⬅️ Orqaga", callback_data="boss:back")
    builder.adjust(3, 1)
    return builder.as_markup()


def orders_nav_keyboard(offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if offset > 0:
        builder.button(text="◀️ Oldingi", callback_data=f"boss:orders:{offset - 10}")
    if has_more:
        builder.button(text="Keyingi ▶️", callback_data=f"boss:orders:{offset + 10}")
    builder.button(text="⬅️ Orqaga", callback_data="boss:back")
    builder.adjust(2, 1)
    return builder.as_markup()


# kept for backward compat
def reports_nav_keyboard(offset: int, has_more: bool) -> InlineKeyboardMarkup:
    return orders_nav_keyboard(offset, has_more)


def users_list_keyboard(users: list[dict], action_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for u in users:
        builder.button(text=f"👤 {u['full_name']}", callback_data=f"{action_prefix}:{u['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="boss:back")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_user_keyboard(user_id: int, confirm_cb: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"{confirm_cb}:{user_id}")
    builder.button(text="❌ Bekor qilish", callback_data="boss:back")
    builder.adjust(2)
    return builder.as_markup()


def back_to_boss() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="boss:back")
    builder.adjust(1)
    return builder.as_markup()
