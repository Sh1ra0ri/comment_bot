from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def rules_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить новое правило", callback_data="rule:add")],
            [InlineKeyboardButton(text="📋 Смотреть правила", callback_data="rule:list")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )


def rules_list_kb(rules: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=r["name"], callback_data=f"rule:{r['id']}:open")] for r in rules]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:rules")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rule_card_kb(rule_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"rule:{rule_id}:edit:name")],
            [InlineKeyboardButton(text="✏️ Изменить ключевое слово", callback_data=f"rule:{rule_id}:edit:keyword")],
            [InlineKeyboardButton(text="✏️ Изменить сообщение", callback_data=f"rule:{rule_id}:edit:message")],
            [InlineKeyboardButton(text="🔗 Изменить привязанные аккаунты", callback_data=f"rule:{rule_id}:accounts")],
            [InlineKeyboardButton(text="🗑 Удалить правило", callback_data=f"rule:{rule_id}:delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="rule:list")],
        ]
    )


def rule_accounts_kb(rule_id: int, accounts: list[dict], linked_ids: set[int]) -> InlineKeyboardMarkup:
    rows = []
    for acc in accounts:
        mark = "✅" if acc["id"] in linked_ids else "▫️"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} @{acc['username']}",
                    callback_data=f"rule:{rule_id}:toggle_acc:{acc['id']}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rule:{rule_id}:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def attach_choice_kb(rule_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"rule:{rule_id}:attach:yes"),
                InlineKeyboardButton(text="Нет", callback_data=f"rule:{rule_id}:attach:no"),
            ]
        ]
    )


def attach_accounts_list_kb(rule_id: int, accounts: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"@{a['username']}", callback_data=f"rule:{rule_id}:attach_pick:{a['id']}")]
        for a in accounts
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:rules")])
    return InlineKeyboardMarkup(inline_keyboard=rows)