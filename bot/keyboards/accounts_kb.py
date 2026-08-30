from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def accounts_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="acc:add")],
            [InlineKeyboardButton(text="📋 Список аккаунтов", callback_data="acc:list")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )


def accounts_list_kb(accounts: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for acc in accounts:
        label = f"@{acc['username']}"
        if acc["needs_reauth"]:
            label = f"⚠️ {label}"
        elif not acc["is_active"]:
            label = f"🔴 {label}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"acc:{acc['id']}:open")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:accounts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def account_card_kb(account: dict) -> InlineKeyboardMarkup:
    if account["is_active"]:
        toggle_text = "🔴 Деактивировать"
        toggle_cb = f"acc:{account['id']}:deactivate"
    else:
        toggle_text = "🟢 Активировать"
        toggle_cb = f"acc:{account['id']}:activate"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"acc:{account['id']}:delete")],
            [InlineKeyboardButton(text=toggle_text, callback_data=toggle_cb)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="acc:list")],
        ]
    )