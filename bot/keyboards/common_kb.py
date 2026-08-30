from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Аккаунты", callback_data="menu:accounts")],
            [InlineKeyboardButton(text="⚙️ Правила", callback_data="menu:rules")],
            [InlineKeyboardButton(text="👥 Администраторы", callback_data="menu:admins")],
        ]
    )


def yes_no_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=yes_cb),
                InlineKeyboardButton(text="Нет", callback_data=no_cb),
            ]
        ]
    )


def back_kb(cb: str, text: str = "⬅️ Назад") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=cb)]])


def cancel_kb(cb: str = "rule_create:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отменить", callback_data=cb)]])


def back_and_cancel_kb(back_cb: str, cancel_cb: str = "rule_create:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)],
            [InlineKeyboardButton(text="Отменить", callback_data=cancel_cb)],
        ]
    )