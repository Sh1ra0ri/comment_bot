from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from db import admins as db_admins
from bot.keyboards.admins_kb import admin_remove_confirm_kb, admins_list_kb, admins_menu_kb
from bot.keyboards.common_kb import back_kb
from bot.states import AdminAdd

router = Router()


@router.callback_query(F.data == "menu:admins")
async def cb_admins_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Администраторы:", reply_markup=admins_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admins:list")
async def cb_admins_list(callback: CallbackQuery) -> None:
    admins = await db_admins.list_admins()
    await callback.message.edit_text(
        "Администраторы:",
        reply_markup=admins_list_kb(admins, settings.super_admin_id),
    )
    await callback.answer()


@router.callback_query(F.data == "admins:add")
async def cb_admins_add_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminAdd.waiting_id)
    await callback.message.edit_text(
        "Перешлите сообщение от нового администратора или отправьте его Telegram ID.",
        reply_markup=back_kb("menu:admins", text="Отменить"),
    )
    await callback.answer()


@router.message(AdminAdd.waiting_id)
async def save_new_admin(message: Message, state: FSMContext) -> None:
    if message.forward_from:
        new_id = message.forward_from.id
    elif message.text and message.text.strip().lstrip("-").isdigit():
        new_id = int(message.text.strip())
    else:
        await message.answer(
            "Не удалось распознать ID. Перешлите сообщение от пользователя или отправьте его числовой Telegram ID."
        )
        return

    await db_admins.add_admin(new_id, added_by=message.from_user.id)
    await state.clear()
    await message.answer(f"Администратор {new_id} добавлен ✅", reply_markup=admins_menu_kb())


# ---------- удаление администратора ----------


@router.callback_query(F.data.startswith("admins:remove_confirm:"))
async def cb_admin_remove_confirm(callback: CallbackQuery) -> None:
    telegram_id = int(callback.data.split(":")[2])

    if telegram_id == callback.from_user.id:
        await callback.answer("Нельзя удалить самого себя ⚠️", show_alert=True)
        return
    if telegram_id == settings.super_admin_id:
        await callback.answer("Нельзя удалить главного администратора ⚠️", show_alert=True)
        return

    await callback.message.edit_text(
        "⚠️ Удалить этого администратора?",
        reply_markup=admin_remove_confirm_kb(telegram_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admins:remove_yes:"))
async def cb_admin_remove_yes(callback: CallbackQuery) -> None:
    telegram_id = int(callback.data.split(":")[2])

    if telegram_id == callback.from_user.id:
        await callback.answer("Нельзя удалить самого себя ⚠️", show_alert=True)
        return
    if telegram_id == settings.super_admin_id:
        await callback.answer("Нельзя удалить главного администратора ⚠️", show_alert=True)
        return
    if await db_admins.count_admins() <= 1:
        await callback.answer("Нельзя удалить последнего администратора ⚠️", show_alert=True)
        return

    await db_admins.remove_admin(telegram_id)
    await callback.answer("Удалён")
    admins = await db_admins.list_admins()
    await callback.message.edit_text(
        "Администратор удалён ✅",
        reply_markup=admins_list_kb(admins, settings.super_admin_id),
    )