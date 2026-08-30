from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admins_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить администратора", callback_data="admins:add")],
            [InlineKeyboardButton(text="📋 Список администраторов", callback_data="admins:list")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )


def admins_list_kb(admins: list[dict], super_admin_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗑 {a['telegram_id']}",
                callback_data=f"admins:remove_confirm:{a['telegram_id']}",
            )
        ]
        for a in admins
        if a["telegram_id"] != super_admin_id
    ]
    rows.append([InlineKeyboardButton(text="➕ Добавить администратора", callback_data="admins:add")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:admins")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_remove_confirm_kb(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"admins:remove_yes:{telegram_id}")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="admins:list")],
        ]
    )