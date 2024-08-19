import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.models import Habit
from habit_bot.button_menu import (
    get_habit_list_menu,
    get_habit_info_menu,
    get_user_menu,
    get_confirmation_del_habit,
    create_user_menu,
    create_update_keyboard, update_user_keyboard, edit_profile_menu
)
from habit_bot.crud.habit.delete_habit import habit_delete
from habit_bot.crud.habit.habit_info import get_habit_info_by_id
from habit_bot.crud.habit.habit_list import get_habit_list
from habit_bot.crud.habit.update_habit import save_update_habit
from habit_bot.crud.users.update_user_data import update_user_data
from habit_bot.crud.users.user_info import get_user_info
from habit_bot.states_group.states import (
    CreateHabit, UserEntry,
    UserRegistration,
    UpdateHabit,
    UpdateProfile,
)
from habit_bot.bot_init import bot
from services.handlers import (
    mark_habit_completed,
    mark_habit_not_completed,
    get_habit_by_id,
    record_message_id,
    clear_message_in_chat,
    delete_job_reminder,
    get_not_completed_habit_list,
    save_update_user_data,
)

logger: logging.Logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda call: call.data in ["main_menu"])
async def handle_main_menu(call: CallbackQuery):
    """
    Обработчик для команды "main_menu", который отображает главное меню для пользователя.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram из объекта обратного вызова.
    2. Если данные обратного вызова соответствуют "main_menu":
       - Удаление сообщения с кнопкой обратного вызова.
       - Очистка всех сообщений в чате, связанных с данным пользователем.
       - Отправка нового сообщения с главным меню.
       - Запись идентификатора нового сообщения в базу данных для последующего управления.

    Исключения:
    - В случае неудачи удаления сообщения с кнопкой обратного вызова, логируется предупреждение.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    if call.data == "main_menu":
        try:
            # Удаление команды от кнопки
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")

        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        sent_message = await call.message.answer("Главное меню:", reply_markup=await create_user_menu())
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        # sent_message_ids.append(sent_message.message_id)


# Блок входа и регистрации нового пользователя.
@router.callback_query(lambda call: call.data in ["sign_in", "profile"])
async def handle_main_menu(call: CallbackQuery, state: FSMContext):
    """
    Обработчик для команд "sign_in" и "profile", который переключает состояние пользователя и запрашивает ввод имени и фамилии.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.
    state (FSMContext): Контекст состояния конечного автомата, используемый для управления состояниями пользователя.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram из объекта обратного вызова.
    2. В зависимости от значения данных обратного вызова:
       - "sign_in": установка состояния `UserEntry.nickname` и запрос ввода имени и фамилии.
       - "profile": установка состояния `UserRegistration.nickname` и запрос ввода имени и фамилии.
    3. Запись идентификатора нового сообщения в базу данных для последующего управления.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    if call.data == "sign_in":
        await state.set_state(UserEntry.nickname)
        sent_message = await call.message.answer("Введите ваше имя и фамилию:")
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        # sent_message_ids.append(sent_message.message_id)
    elif call.data == "profile":
        await state.set_state(UserRegistration.nickname)
        sent_message = await call.message.answer("Введите ваше имя и фамилию:")
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        # sent_message_ids.append(sent_message.message_id)


# Блок меню пользователя (создать привычку, текущие привычки, сформированные привычки, мои достижения).
@router.callback_query(
    lambda call: call.data in [
        "add_habit",
        "process_habit",
        "my_habit",
        "achievements",
        "main_user_menu",
    ])
async def handle_main_menu(call: CallbackQuery, state: FSMContext):
    """
   Обработчик для различных команд меню пользователя, переключающий состояние пользователя
   и выполняющий соответствующие действия в зависимости от команды.

   Parameters:
   call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.
   state (FSMContext): Контекст состояния конечного автомата, используемый для управления состояниями пользователя.

   Процедура выполнения:
   1. Получение идентификатора пользователя Telegram из объекта обратного вызова.
   2. В зависимости от значения данных обратного вызова, выполняется соответствующее действие:
      - "add_habit": установка состояния `CreateHabit.habit_name` и запрос ввода названия привычки.
      - "process_habit": получение списка текущих привычек пользователя и отображение их меню.
      - "main_user_menu": отображение основного меню пользователя.
   3. Запись идентификатора нового сообщения в базу данных для последующего управления.

   Returns:
   None
   """
    bot_user_id = call.from_user.id
    logger.info(f"USER ID bot_user_id - {bot_user_id}")
    if call.data == "add_habit":
        try:
            # Удаление команды от кнопки
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        await state.set_state(CreateHabit.habit_name)
        sent_message = await call.message.answer("Введите название привычки:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
    elif call.data == "process_habit":
        try:
            # Удаление команды от кнопки
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
        await clear_message_in_chat(call.message.chat.id, bot_user_id)

        habit_list = await get_not_completed_habit_list(bot_user_id)
        if habit_list != []:
            habit_menu = await get_habit_list_menu(habit_list)
            sent_message = await call.message.answer(
                "*Ваши текущие привычки:*\n_Для получения подробной информации нажмите на кнопку с названием привычки_",
                reply_markup=habit_menu, parse_mode="Markdown"
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        else:
            sent_message = await call.message.answer("У вас нет ни одной незавершенной привычки!",
                                                reply_markup=await create_user_menu())
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)

    elif call.data == "main_user_menu":
        try:
            # Удаление команды от кнопки
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        sent_message = await call.message.answer(
            "*Выберите нужное действие:*", reply_markup=get_user_menu(), parse_mode="Markdown"
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


@router.callback_query(lambda call: call.data.startswith("habit_item_"))
async def handle_habit_item(call: CallbackQuery):
    """
    Обработчик для взаимодействия с элементами привычек, отображающих информацию о привычке и
    предоставляющих меню действий.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram и идентификатора привычки из данных обратного вызова.
    2. Получение информации о привычке по идентификатору.
    3. Удаление сообщения с командой кнопки.
    4. Очистка сообщений в чате для данного пользователя.
    5. Отправка нового сообщения с информацией о привычке и меню действий.
    6. Запись идентификатора нового сообщения в базу данных для последующего управления.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    habit_id = int(call.data.split("_")[2])
    habit_info = await get_habit_info_by_id(habit_id)

    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)


    sent_message = await bot.send_message(
        call.message.chat.id, f"{habit_info}", parse_mode="Markdown", reply_markup=await get_habit_info_menu(habit_id))
    await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


# Обработчик для динамических кнопок привычек
@router.callback_query(lambda call: call.data.startswith("delete_habit_"))
async def handle_habit_item(call: CallbackQuery):
    """
   Обработчик для удаления привычки пользователя.

   Parameters:
   call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

   Процедура выполнения:
   1. Получение идентификатора пользователя Telegram и идентификатора привычки из данных обратного вызова.
   2. Получение информации о привычке по идентификатору.
   3. Удаление сообщения с командой кнопки.
   4. Очистка сообщений в чате для данного пользователя.
   5. Если информация о привычке получена, отправка нового сообщения с подтверждением удаления и меню действий.
   6. Если получение информации о привычке завершилось ошибкой, отправка сообщения об ошибке.
   7. Запись идентификатора нового сообщения в базу данных для последующего управления.

   Returns:
   None
   """
    bot_user_id = call.message.from_user.id
    habit_id = int(call.data.split("_")[2])
    response = await get_habit_by_id(habit_id)
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    if isinstance(response, Habit):
        sent_message = await bot.send_message(
            call.message.chat.id,
            f"*Вы точно хотите удалить привычку:* {response.habit_name}",
            parse_mode="Markdown",
            reply_markup=await get_confirmation_del_habit(habit_id),
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
    else:
        sent_message = await bot.send_message(call.message.chat.id, f"Ошибка:\n{response}")
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


# Обработка подтверждения удаления.
@router.callback_query(lambda call: call.data.startswith("confirmation_"))
async def handle_habit_item(call: CallbackQuery):
    """
    Обработчик для подтверждения удаления привычки пользователя.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram и идентификатора привычки из данных обратного вызова.
    2. Удаление привычки по идентификатору.
    3. Удаление сообщения с командой кнопки.
    4. Очистка сообщений в чате для данного пользователя.
    5. Если привычка успешно удалена:
       - Отправка сообщения о успешном удалении.
       - Отправка сообщения с главным меню пользователя.
       - Удаление напоминания для привычки.
    6. Если удаление привычки завершилось ошибкой:
       - Отправка сообщения об ошибке.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    habit_id = int(call.data.split("_")[1])
    success = await habit_delete(habit_id)
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    if success:
        sent_message = await bot.send_message(
            call.message.chat.id, f"Привычка успешно удалена!")
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        sent_message = await call.message.answer(
            "*Выберите нужное действие:*", reply_markup=get_user_menu(), parse_mode="Markdown"
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        try:
            # Удаление команды от кнопки
            await delete_job_reminder(habit_id)
            logger.info(f"Запись напоминания для привычки - {habit_id} успешно удалена.")
        except Exception as e:
            logger.warning(f"При удалении записи напоминания привычки - {habit_id} произошла ошибка :{e}")
        await clear_message_in_chat(call.message.chat.id, bot_user_id)

    else:
        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        sent_message = await bot.send_message(
            call.message.chat.id, f"При удалении возникла непредвиденная ошибка")
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


# Обработка команды, если передумал удалять привычку.
@router.callback_query(lambda call: call.data.startswith("not_confirmation"))
async def handle_habit_item(call: CallbackQuery):
    """
    Обработчик для отмены подтверждения удаления привычки пользователя и возврата к списку привычек.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram.
    2. Удаление сообщения с командой кнопки.
    3. Очистка сообщений в чате для данного пользователя.
    4. Получение списка привычек пользователя.
    5. Создание меню с текущими привычками пользователя.
    6. Отправка сообщения с текущими привычками и возможностью выбрать подробную информацию о каждой.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    habit_list = await get_habit_list()
    habit_menu = await get_habit_list_menu(habit_list)

    sent_message = await call.message.answer(
        "*Ваши текущие привычки:*\n_Для получения подробной информации нажмите на кнопку с названием привычки_",
        reply_markup=habit_menu, parse_mode="Markdown"
    )
    await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)



@router.callback_query(
    lambda call: call.data.startswith("habit_complected_")
                 or call.data.startswith("habit_not_complected_")
)
async def handle_habit_item(call: CallbackQuery):
    """
    Обработчик для отметки привычек как выполненных или невыполненных.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram.
    2. Разделение данных обратного вызова для определения действия (выполнено или не выполнено).
    3. Удаление сообщения с командой кнопки.
    4. Очистка сообщений в чате для данного пользователя.
    5. В зависимости от действия, отметка привычки как выполненной или невыполненной.
    6. Получение информации о привычке и отправка сообщения с обновленной информацией.
    7. В случае, если действие неизвестно, отправка сообщения с меню пользователя.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    data_parts = call.data.split("_")
    action = data_parts[1]
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    if action == "complected":
        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        habit_id = int(data_parts[2])
        complected = await mark_habit_completed(habit_id)
        if complected:
            habit_info = await get_habit_info_by_id(habit_id)
            sent_message = await bot.send_message(
                call.message.chat.id, f"{habit_info}",
                reply_markup=await get_habit_info_menu(habit_id),
                parse_mode="Markdown",
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)

        else:
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            habit_info = await get_habit_info_by_id(habit_id)
            sent_message = await bot.send_message(
                call.message.chat.id,
                f"*Сегодня вы уже ставили отметку этому заданию.*\n{habit_info}",
                reply_markup=await get_habit_info_menu(habit_id),
                parse_mode="Markdown",
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
    elif action == "not":
        habit_id = int(data_parts[3])
        not_complected = await mark_habit_not_completed(habit_id)
        await clear_message_in_chat(call.message.chat.id, bot_user_id)
        if not_complected:
            habit_info = await get_habit_info_by_id(habit_id)
            sent_message = await bot.send_message(
                call.message.chat.id, f"{habit_info}",
                reply_markup=await get_habit_info_menu(habit_id),
                parse_mode="Markdown",
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        else:
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            habit_info = await get_habit_info_by_id(habit_id)
            sent_message = await bot.send_message(
                call.message.chat.id,
                f"*Сегодня вы уже ставили отметку этому заданию.*\n{habit_info}",
                reply_markup=await get_habit_info_menu(habit_id),
                parse_mode="Markdown",
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
    else:
        sent_message = await bot.send_message(
            call.message.chat.id,
            "Неизвестное действие.",
            reply_markup=get_user_menu(),
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


@router.callback_query(
    lambda call: call.data.startswith("update_habit_"))
async def handle_habit_item(call: CallbackQuery):
    """
    Обработчик для обновления информации о привычке.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram.
    2. Удаление сообщения с командой кнопки и очистка сообщений в чате для данного пользователя.
    3. Разделение данных обратного вызова для получения идентификатора привычки.
    4. Получение информации о привычке по ее идентификатору.
    5. Отправка сообщения с информацией о привычке и клавиатурой для обновления привычки.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)


    data_parts = call.data.split("_")
    habit_id = data_parts[2]
    logger.info(f"Habit update - {habit_id}")
    habit_info = await get_habit_info_by_id(int(habit_id))

    sent_message = await bot.send_message(
        call.message.chat.id, f"*Выберите что хотите изменить.*\n{habit_info}",
        reply_markup=await create_update_keyboard(habit_id),
        parse_mode="Markdown"
    )
    await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


# Обработка функции редактирования привычек
@router.callback_query(
    lambda call: call.data.startswith("habit_name_") or
                 call.data.startswith("habit_description_") or
                 call.data.startswith("all_duration_") or
                 call.data.startswith("reminder_time_") or
                 call.data.startswith("update_save_")
)
async def update_habit_callback(call: CallbackQuery, state: FSMContext):
    """
    Обработчик для обновления информации о привычке.

    Parameters:
    call (CallbackQuery): Объект обратного вызова Telegram, содержащий информацию о сообщении и данных обратного вызова.
    state (FSMContext): Контекст состояния для управления состояниями пользователя.

    Процедура выполнения:
    1. Получение идентификатора пользователя Telegram.
    2. Удаление сообщения с командой кнопки и очистка сообщений в чате для данного пользователя.
    3. Логирование начала обработки обновления привычки.
    4. Разделение данных обратного вызова для получения идентификатора привычки и обновление состояния.
    5. В зависимости от типа действия (название, описание, длительность, время напоминания, сохранение):
       - Запрашивает соответствующую информацию у пользователя.
       - Обновляет состояние пользователя для дальнейшей обработки.
    6. При успешном обновлении привычки отправляет подтверждение, в противном случае сообщает об ошибке.

    Returns:
    None
    """
    bot_user_id = call.message.from_user.id
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    logger.info(f"Start update_habit_callback")
    data_parts = call.data.split("_")
    habit_id = data_parts[2]
    await state.update_data(habit_id=habit_id)

    if call.data.startswith("habit_name_"):
        sent_message = await call.message.answer("Введите название привычки:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateHabit.habit_name)

    elif call.data.startswith("habit_description_"):
        sent_message = await call.message.answer("Введите описание привычки:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateHabit.habit_description)

    elif call.data.startswith("all_duration_"):
        sent_message = await call.message.answer(
            "Укажите планируемое количество дней выполнения заданий _Например 15 или 21_: ",
            parse_mode='Markdown'
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateHabit.all_duration)

    elif call.data.startswith("reminder_time_"):
        sent_message = await call.message.answer(
            "В какое время отправить напоминание?\n _Например 16:00 или 10:30_",
            parse_mode='Markdown'
        )
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateHabit.reminder_time)

    elif call.data.startswith("update_save_"):
        upd_habit = await save_update_habit(state)
        if upd_habit:
            habit_list = await get_habit_list()
            habit_menu = await get_habit_list_menu(habit_list)
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            sent_message = await call.message.answer(
                f"Привычка '{upd_habit.habit_name}' успешно обновлена.",
                reply_markup=habit_menu, parse_mode='Markdown')
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        else:
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            sent_message = await call.message.answer("Ошибка при обновлении привычки.")
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


@router.callback_query(
    lambda call: call.data.startswith("edit_profile_"))
async def handle_edit_profile(call: CallbackQuery):
    data_parts = call.data.split("_")
    bot_user_id = int(data_parts[2])
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)
    sent_message = await bot.send_message(
        call.message.chat.id, f"*Выберите что хотите изменить.*\n",
        reply_markup=await update_user_keyboard(bot_user_id),
        parse_mode="Markdown"
    )
    await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)


@router.callback_query(
    lambda call: call.data.startswith("user_name_") or
                 call.data.startswith("user_age_") or
                 call.data.startswith("user_phone_") or
                 call.data.startswith("user_mail_") or
                 call.data.startswith("user_city_") or
                call.data.startswith("save_user_data_")
)
async def update_habit_callback(call: CallbackQuery, state: FSMContext):
    bot_user_id = call.from_user.id
    await state.update_data(bot_user_id=bot_user_id)
    try:
        # Удаление команды от кнопки
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {call.message.message_id}: {e}")
    await clear_message_in_chat(call.message.chat.id, bot_user_id)

    if call.data.startswith("user_name_"):
        sent_message = await call.message.answer("Введите имя:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateProfile.fullname)

    elif call.data.startswith("user_age_"):
        sent_message = await call.message.answer("Введите возраст:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateProfile.age)

    elif call.data.startswith("user_phone_"):
        sent_message = await call.message.answer("Введите номер телефона:", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateProfile.phone)

    elif call.data.startswith("user_mail_"):
        sent_message = await call.message.answer("Введите адрес электронной почты", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateProfile.email)

    elif call.data.startswith("user_city_"):
        sent_message = await call.message.answer("Введите город", parse_mode='Markdown')
        await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        await state.set_state(UpdateProfile.city)

    elif call.data.startswith("save_user_data_"):
        bot_user_id = call.from_user.id
        upd_user = await update_user_data(state)
        if upd_user:
            user_info = await get_user_info(bot_user_id)
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            sent_message = await call.message.answer(
                f"Данные успешно обновлены!\n{user_info}",
                reply_markup=await edit_profile_menu(bot_user_id),
                parse_mode='Markdown'
            )
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
        else:
            await clear_message_in_chat(call.message.chat.id, bot_user_id)
            sent_message = await call.message.answer("Ошибка при обновлении данных.")
            await record_message_id(call.message.chat.id, sent_message.message_id, bot_user_id)
