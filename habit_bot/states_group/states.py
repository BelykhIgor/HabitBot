from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


class UserRegistration(StatesGroup):
    """
    Группа состояний для регистрации пользователя.

    Этот класс определяет состояния, через которые проходит пользователь
    во время регистрации в системе.

    Состояния:
        nickname: Состояние для ввода полного имени пользователя.
        phone: Состояние для ввода номера телефона.
        age: Состояние для ввода возраста.
        email: Состояние для ввода адреса электронной почты.
        password: Состояние для ввода пароля.
    """
    nickname = State()
    phone = State()
    age = State()
    email = State()
    password = State()


class UserEntry(StatesGroup):
    """
    Группа состояний для входа пользователя.

    Этот класс определяет состояния, через которые проходит пользователь
    во время входа в систему.

    Состояния:
        nickname: Состояние для ввода полного имени пользователя.
        user_id: Состояние для ввода идентификатора пользователя.
        password: Состояние для ввода пароля.
    """
    nickname = State()
    user_id = State()
    password = State()


class CreateHabit(StatesGroup):
    """
    Группа состояний для создания привычки.

    Этот класс определяет состояния, через которые проходит пользователь
    во время создания новой привычки.

    Состояния:
        habit_name: Состояние для ввода названия привычки.
        duration: Состояние для ввода продолжительности выполнения привычки.
        comments: Состояние для ввода комментариев к привычке.
        reminder_time: Состояние для выбора времени напоминания о привычке.
    """
    habit_name = State()
    duration = State()
    comments = State()
    reminder_time = State()


class UpdateHabit(StatesGroup):
    """
    Группа состояний для обновления привычки.

    Этот класс определяет состояния, через которые проходит пользователь
    во время обновления существующей привычки.

    Состояния:
       habit_id: Состояние для ввода идентификатора привычки, которую нужно обновить.
       habit_name: Состояние для ввода нового названия привычки.
       all_duration: Состояние для ввода новой продолжительности привычки.
       habit_description: Состояние для ввода нового описания привычки.
       reminder_time: Состояние для ввода нового времени напоминания.
       save_update: Состояние для подтверждения обновления привычки.
    """
    habit_id = State()
    habit_name = State()
    all_duration = State()
    habit_description = State()
    reminder_time = State()
    save_update = State()


class UpdateProfile(StatesGroup):
    bot_user_id = State()
    fullname = State()
    age = State()
    phone = State()
    email = State()
    city = State()
    save_update = State()