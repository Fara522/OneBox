from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Boss", callback_data="role:boss")
    builder.button(text="⚙️ Admin", callback_data="role:admin")
    builder.button(text="👷 Ishchi", callback_data="role:worker")
    builder.button(text="📋 Buyurtmachi", callback_data="role:customer")
    builder.adjust(2, 2)
    return builder.as_markup()


# backward-compat aliases
def who_are_you_keyboard() -> InlineKeyboardMarkup:
    return start_keyboard()


def user_names_keyboard(users: list[dict], back_cb: str = "back_to_start") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for u in users:
        builder.button(text=f"👤 {u['full_name']}", callback_data=f"select_name:{u['id']}")
    builder.button(text="⬅️ Orqaga", callback_data=back_cb)
    builder.adjust(1)
    return builder.as_markup()


def worker_names_keyboard(users: list[dict]) -> InlineKeyboardMarkup:
    return user_names_keyboard(users)


def machines_keyboard(machines: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in machines:
        builder.button(text=f"🏭 {m['name']}", callback_data=f"machine:{m['id']}")
    builder.adjust(1)
    return builder.as_markup()


def worker_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Buyurtmalar", callback_data="worker:orders")
    builder.button(text="🚪 Chiqish", callback_data="logout")
    builder.adjust(1)
    return builder.as_markup()


def worker_main_menu_active() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Faol ishim", callback_data="worker:active")
    builder.button(text="📋 Buyurtmalar", callback_data="worker:orders")
    builder.button(text="🚪 Chiqish", callback_data="logout")
    builder.adjust(1)
    return builder.as_markup()


def orders_list_keyboard(orders: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for o in orders:
        icon = "🔴" if o["status"] == "pending" else "🟡"
        text = f"{icon} #{o['id']} {o['product_name']} ({o['quantity']:,} ta)"
        builder.button(text=text, callback_data=f"accept_order:{o['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="worker:back")
    builder.adjust(1)
    return builder.as_markup()


def order_machine_keyboard(machines: list[dict], order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in machines:
        builder.button(text=f"🏭 {m['name']}", callback_data=f"select_machine:{order_id}:{m['id']}")
    builder.button(text="⬅️ Orqaga", callback_data="worker:orders")
    builder.adjust(1)
    return builder.as_markup()


def skip_helper_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Yordamchisiz ishlash", callback_data="skip_helper")
    builder.button(text="❌ Bekor qilish", callback_data="worker:back")
    builder.adjust(1)
    return builder.as_markup()


def working_order_keyboard(stage_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Keyingi bosqich", callback_data=f"next_stage:{stage_id}")
    builder.button(text="✅ Tugadi", callback_data=f"done_order:{stage_id}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_finish_keyboard(stage_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, tugadi (yakunlash)", callback_data=f"confirm_done:{stage_id}")
    builder.button(text="⏭ Keyingi bosqichga o'tish", callback_data=f"confirm_next:{stage_id}")
    builder.button(text="⬅️ Orqaga", callback_data=f"worker:active")
    builder.adjust(1)
    return builder.as_markup()


# Old report keyboards (kept for compat)
def skip_assistant_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ O'tkazib yuborish", callback_data="skip_assistant")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_form")
    builder.adjust(1)
    return builder.as_markup()


def confirm_start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ ISHNI BOSHLASH", callback_data="confirm_start")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_form")
    builder.adjust(1)
    return builder.as_markup()


def working_keyboard(report_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏹ ISHNI TUGATISH", callback_data=f"stop_work:{report_id}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_stop_keyboard(report_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, tugatildi", callback_data=f"confirm_stop:{report_id}")
    builder.button(text="⬅️ Davom etish", callback_data=f"back_working:{report_id}")
    builder.adjust(2)
    return builder.as_markup()
