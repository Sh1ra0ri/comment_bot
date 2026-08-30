from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import accounts as db_accounts
from db import rule_accounts as db_rule_accounts
from db import rules as db_rules
from bot.keyboards.common_kb import back_kb, cancel_kb, back_and_cancel_kb, yes_no_kb
from bot.keyboards.rules_kb import (
    attach_accounts_list_kb,
    attach_choice_kb,
    rule_accounts_kb,
    rule_card_kb,
    rules_list_kb,
    rules_menu_kb,
)
from bot.states import RuleCreation, RuleEdit

router = Router()


def _rule_card_text(rule: dict, linked: list[dict]) -> str:
    accounts_text = "\n".join(f"@{a['username']}" for a in linked) if linked else "Нет"
    return (
        f"Правило: {rule['name']}\n\n"
        f"Ключевое слово:\n{rule['keyword']}\n\n"
        f"Сообщение:\n{rule['message']}\n\n"
        f"Привязанные аккаунты:\n{accounts_text}"
    )


# ---------- меню правил ----------


@router.callback_query(F.data == "menu:rules")
async def cb_rules_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Правила:", reply_markup=rules_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "rule:list")
async def cb_rules_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    rules = await db_rules.list_rules()
    if not rules:
        await callback.message.edit_text("Правил пока нет.", reply_markup=rules_menu_kb())
    else:
        await callback.message.edit_text("Список правил:", reply_markup=rules_list_kb(rules))
    await callback.answer()


# ---------- создание правила (FSM) ----------


@router.callback_query(F.data == "rule:add")
async def cb_add_prompt(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Хотите добавить новое правило?",
        reply_markup=yes_no_kb("rule_create:yes", "rule_create:no"),
    )
    await callback.answer()


@router.callback_query(F.data == "rule_create:no")
async def cb_add_no(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Правила:", reply_markup=rules_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "rule_create:yes")
async def cb_add_yes(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RuleCreation.name)
    await callback.message.edit_text(
        "Шаг 1\nВведите название правила.\nОно будет видно только вам.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "rule_create:cancel")
async def cb_create_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Создание правила отменено.", reply_markup=rules_menu_kb())
    await callback.answer()


@router.message(RuleCreation.name)
async def step_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(RuleCreation.keyword)
    await message.answer(
        "Шаг 2\nВведите ключевое слово, которое пользователи будут писать в комментариях.",
        reply_markup=back_and_cancel_kb("rule_create:back_to_name"),
    )


@router.callback_query(F.data == "rule_create:back_to_name")
async def cb_back_to_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RuleCreation.name)
    data = await state.get_data()
    current = data.get("name", "")
    await callback.message.edit_text(
        f"Шаг 1\nВведите название правила.\nОно будет видно только вам.\n\n(Текущее значение: {current})",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(RuleCreation.keyword)
async def step_keyword(message: Message, state: FSMContext) -> None:
    await state.update_data(keyword=message.text)
    await state.set_state(RuleCreation.message)
    await message.answer(
        "Шаг 3\nВведите сообщение, которое будет отправляться пользователю в Direct.",
        reply_markup=back_and_cancel_kb("rule_create:back_to_keyword"),
    )


@router.callback_query(F.data == "rule_create:back_to_keyword")
async def cb_back_to_keyword(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RuleCreation.keyword)
    data = await state.get_data()
    current = data.get("keyword", "")
    await callback.message.edit_text(
        "Шаг 2\nВведите ключевое слово, которое пользователи будут писать в комментариях.\n\n"
        f"(Текущее значение: {current})",
        reply_markup=back_and_cancel_kb("rule_create:back_to_name"),
    )
    await callback.answer()


@router.message(RuleCreation.message)
async def step_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    rule_id = await db_rules.create_rule(name=data["name"], keyword=data["keyword"], message=message.text)
    await state.clear()
    await message.answer("Правило успешно создано.")
    await message.answer(
        "Хотите привязать аккаунты к этому правилу?",
        reply_markup=attach_choice_kb(rule_id),
    )


# ---------- карточка правила ----------


@router.callback_query(F.data.regexp(r"^rule:(\d+):open$"))
async def cb_rule_open(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    rule_id = int(callback.data.split(":")[1])
    rule = await db_rules.get_rule(rule_id)
    if not rule:
        await callback.answer("Правило не найдено.", show_alert=True)
        rules = await db_rules.list_rules()
        await callback.message.edit_text(
            "Список правил:" if rules else "Правил пока нет.",
            reply_markup=rules_list_kb(rules) if rules else rules_menu_kb(),
        )
        return
    linked = await db_rules.rule_accounts(rule_id)
    await callback.message.edit_text(_rule_card_text(rule, linked), reply_markup=rule_card_kb(rule_id))
    await callback.answer()


# ---------- редактирование полей правила ----------

FIELD_PROMPTS = {
    "name": "Введите новое название правила.",
    "keyword": "Введите новое ключевое слово.",
    "message": "Введите новое сообщение.",
}


@router.callback_query(F.data.regexp(r"^rule:(\d+):edit:(name|keyword|message)$"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    _, rule_id, _, field = callback.data.split(":")
    await state.set_state(RuleEdit.waiting_value)
    await state.update_data(rule_id=int(rule_id), field=field)
    await callback.message.edit_text(
        FIELD_PROMPTS[field],
        reply_markup=back_kb(f"rule:{rule_id}:open", text="Отменить"),
    )
    await callback.answer()


@router.message(RuleEdit.waiting_value)
async def save_edit_field(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    rule_id, field = data["rule_id"], data["field"]
    await db_rules.update_rule_field(rule_id, field, message.text)
    await state.clear()
    rule = await db_rules.get_rule(rule_id)
    linked = await db_rules.rule_accounts(rule_id)
    await message.answer(_rule_card_text(rule, linked), reply_markup=rule_card_kb(rule_id))


# ---------- удаление правила ----------


@router.callback_query(F.data.regexp(r"^rule:(\d+):delete$"))
async def cb_delete_prompt(callback: CallbackQuery) -> None:
    rule_id = int(callback.data.split(":")[1])
    rule = await db_rules.get_rule(rule_id)
    if not rule:
        await callback.answer("Правило не найдено.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Удалить правило «{rule['name']}»?",
        reply_markup=yes_no_kb(f"rule:{rule_id}:delete:yes", f"rule:{rule_id}:open"),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):delete:yes$"))
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    rule_id = int(callback.data.split(":")[1])
    await db_rules.delete_rule(rule_id)
    await callback.answer()
    rules = await db_rules.list_rules()
    await callback.message.edit_text(
        "Правило удалено.",
        reply_markup=rules_list_kb(rules) if rules else rules_menu_kb(),
    )


# ---------- привязка аккаунтов сразу после создания правила ----------


@router.callback_query(F.data.regexp(r"^rule:(\d+):attach:no$"))
async def cb_attach_no(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Правила:", reply_markup=rules_menu_kb())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):attach:yes$"))
async def cb_attach_yes(callback: CallbackQuery) -> None:
    rule_id = int(callback.data.split(":")[1])
    accounts = await db_accounts.list_accounts()
    if not accounts:
        await callback.message.edit_text("Подключённых аккаунтов пока нет.", reply_markup=rules_menu_kb())
        await callback.answer()
        return
    await callback.message.edit_text(
        "Выберите аккаунт для привязки:",
        reply_markup=attach_accounts_list_kb(rule_id, accounts),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):attach_pick:(\d+)$"))
async def cb_attach_pick(callback: CallbackQuery) -> None:
    _, rule_id, _, account_id = callback.data.split(":")
    rule_id, account_id = int(rule_id), int(account_id)
    account = await db_accounts.get_account(account_id)
    rule = await db_rules.get_rule(rule_id)
    if not account or not rule:
        await callback.answer("Не найдено.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Привязать аккаунт @{account['username']} к правилу «{rule['name']}»?",
        reply_markup=yes_no_kb(
            f"rule:{rule_id}:attach_confirm:{account_id}",
            f"rule:{rule_id}:attach:yes",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):attach_confirm:(\d+)$"))
async def cb_attach_confirm(callback: CallbackQuery) -> None:
    _, rule_id, _, account_id = callback.data.split(":")
    rule_id, account_id = int(rule_id), int(account_id)
    rule = await db_rules.get_rule(rule_id)
    try:
        await db_rule_accounts.link_rule_account(rule_id, account_id, rule["keyword"])
    except db_rule_accounts.DuplicateKeywordError:
        await callback.answer(
            "На этом аккаунте уже есть правило с таким же ключевым словом.",
            show_alert=True,
        )
        accounts = await db_accounts.list_accounts()
        await callback.message.edit_text(
            "Выберите аккаунт для привязки:",
            reply_markup=attach_accounts_list_kb(rule_id, accounts),
        )
        return
    await callback.answer()
    await callback.message.edit_text(
        "Аккаунт успешно привязан. Хотите привязать ещё один?",
        reply_markup=attach_choice_kb(rule_id),
    )


# ---------- управление привязками из карточки правила ----------


@router.callback_query(F.data.regexp(r"^rule:(\d+):accounts$"))
async def cb_manage_accounts(callback: CallbackQuery) -> None:
    rule_id = int(callback.data.split(":")[1])
    accounts = await db_accounts.list_accounts()
    if not accounts:
        await callback.answer("Подключённых аккаунтов пока нет.", show_alert=True)
        return
    linked = await db_rules.rule_accounts(rule_id)
    linked_ids = {a["id"] for a in linked}
    await callback.message.edit_text(
        "Нажмите на аккаунт, чтобы привязать/отвязать его от правила:",
        reply_markup=rule_accounts_kb(rule_id, accounts, linked_ids),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^rule:(\d+):toggle_acc:(\d+)$"))
async def cb_toggle_acc(callback: CallbackQuery) -> None:
    _, rule_id, _, account_id = callback.data.split(":")
    rule_id, account_id = int(rule_id), int(account_id)
    rule = await db_rules.get_rule(rule_id)
    already_linked = await db_rule_accounts.is_linked(rule_id, account_id)
    if already_linked:
        await db_rule_accounts.unlink_rule_account(rule_id, account_id)
    else:
        try:
            await db_rule_accounts.link_rule_account(rule_id, account_id, rule["keyword"])
        except db_rule_accounts.DuplicateKeywordError:
            await callback.answer(
                "На этом аккаунте уже есть правило с таким же ключевым словом.",
                show_alert=True,
            )
            return
    accounts = await db_accounts.list_accounts()
    linked = await db_rules.rule_accounts(rule_id)
    linked_ids = {a["id"] for a in linked}
    await callback.answer()
    await callback.message.edit_text(
        "Нажмите на аккаунт, чтобы привязать/отвязать его от правила:",
        reply_markup=rule_accounts_kb(rule_id, accounts, linked_ids),
    )