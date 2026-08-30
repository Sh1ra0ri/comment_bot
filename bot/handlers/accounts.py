from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import settings
from db import accounts as db_accounts
from db import oauth as db_oauth
from bot.keyboards.accounts_kb import account_card_kb, accounts_list_kb, accounts_menu_kb
from bot.keyboards.common_kb import yes_no_kb

router = Router()

@router.callback_query(F.data == "menu:accounts")
async def cb_accounts_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Аккаунты:", reply_markup=accounts_menu_kb())
    await callback.answer()

@router.callback_query(F.data == "acc:add")
async def cb_add_prompt(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Хотите добавить новый аккаунт?",
        reply_markup=yes_no_kb("acc:add:yes", "acc:add:no"),
    )
    await callback.answer()


@router.callback_query(F.data == "acc:add:no")
async def cb_add_no(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Аккаунты:", reply_markup=accounts_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "acc:add:yes")
async def cb_add_yes(callback: CallbackQuery) -> None:
    state_token = await db_oauth.create_state(callback.from_user.id)
    scopes = (
        "instagram_basic,instagram_manage_comments,"
        "instagram_manage_messages,pages_show_list,pages_manage_metadata"
    )
    auth_url = (
        f"https://www.facebook.com/{settings.meta_api_version}/dialog/oauth"
        f"?client_id={settings.meta_app_id}"
        f"&redirect_uri={settings.meta_redirect_uri}"
        f"&state={state_token}"
        f"&scope={scopes}"
    )
    await callback.message.edit_text(
        "Перейдите по ссылке и авторизуйте доступ к вашему Instagram-аккаунту "
        "(через Facebook Business Login):\n\n"
        f"{auth_url}\n\n"
        "После авторизации бот пришлёт подтверждение в этот чат.",
        reply_markup=accounts_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "acc:list")
async def cb_list(callback: CallbackQuery) -> None:
    accs = await db_accounts.list_accounts()
    if not accs:
        await callback.message.edit_text("Аккаунтов пока нет.", reply_markup=accounts_menu_kb())
    else:
        await callback.message.edit_text("Список аккаунтов:", reply_markup=accounts_list_kb(accs))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^acc:(\d+):open$"))
async def cb_open(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    account = await db_accounts.get_account(account_id)
    if not account:
        await callback.answer("Аккаунт не найден.", show_alert=True)
        accs = await db_accounts.list_accounts()
        await callback.message.edit_text(
            "Список аккаунтов:" if accs else "Аккаунтов пока нет.",
            reply_markup=accounts_list_kb(accs) if accs else accounts_menu_kb(),
        )
        return
    if account["needs_reauth"]:
        status = "⚠️ Требуется переподключение"
    elif account["is_active"]:
        status = "🟢 Активен"
    else:
        status = "🔴 Деактивирован"
    await callback.message.edit_text(
        f"Что вы хотите сделать с аккаунтом @{account['username']}?\n\nСтатус: {status}",
        reply_markup=account_card_kb(account),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^acc:(\d+):delete$"))
async def cb_delete_prompt(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    account = await db_accounts.get_account(account_id)
    if not account:
        await callback.answer("Аккаунт не найден.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Удалить аккаунт @{account['username']}?",
        reply_markup=yes_no_kb(f"acc:{account_id}:delete:yes", f"acc:{account_id}:open"),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^acc:(\d+):delete:yes$"))
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    await db_accounts.delete_account(account_id)
    await callback.answer()
    accs = await db_accounts.list_accounts()
    await callback.message.edit_text(
        "Аккаунт удалён.",
        reply_markup=accounts_list_kb(accs) if accs else accounts_menu_kb(),
    )


@router.callback_query(F.data.regexp(r"^acc:(\d+):deactivate$"))
async def cb_deactivate_prompt(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    account = await db_accounts.get_account(account_id)
    if not account:
        await callback.answer("Аккаунт не найден.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Деактивировать аккаунт @{account['username']}?",
        reply_markup=yes_no_kb(f"acc:{account_id}:deactivate:yes", f"acc:{account_id}:open"),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^acc:(\d+):activate$"))
async def cb_activate_prompt(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    account = await db_accounts.get_account(account_id)
    if not account:
        await callback.answer("Аккаунт не найден.", show_alert=True)
        return
    await callback.message.edit_text(
        f"Активировать аккаунт @{account['username']}?",
        reply_markup=yes_no_kb(f"acc:{account_id}:activate:yes", f"acc:{account_id}:open"),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^acc:(\d+):deactivate:yes$"))
async def cb_deactivate_confirm(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    await db_accounts.set_active(account_id, False)
    await callback.answer()
    accs = await db_accounts.list_accounts()
    await callback.message.edit_text(
        "Аккаунт деактивирован.",
        reply_markup=accounts_list_kb(accs) if accs else accounts_menu_kb(),
    )


@router.callback_query(F.data.regexp(r"^acc:(\d+):activate:yes$"))
async def cb_activate_confirm(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    await db_accounts.set_active(account_id, True)
    await callback.answer()
    accs = await db_accounts.list_accounts()
    await callback.message.edit_text(
        "Аккаунт активирован.",
        reply_markup=accounts_list_kb(accs) if accs else accounts_menu_kb(),
    )