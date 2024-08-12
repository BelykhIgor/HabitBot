import re
from datetime import date
from passlib.context import CryptContext
from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, BigInteger
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class User(Base):
    """
    Представляет пользователя в системе.

    Атрибуты:
       id (int): Уникальный идентификатор пользователя.
       nickname (str): Никнейм пользователя.
       profile_id (int): Идентификатор профиля, связанного с пользователем.
       api_key (str): API ключ пользователя.
       profile (Profile): Связанный профиль пользователя.
       followed (list[User]):
       Список пользователей, за которыми данный пользователь следует.
       followers (list[User]):
       Список пользователей, которые следуют за данным пользователем.
    """

    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nickname = Column(String(25), nullable=False)
    fullname = Column(String(25))
    age = Column(String(3), nullable=False)
    phone = Column(String(12))
    email = Column(String(25))
    city = Column(String(25))
    password_hash = Column(String(128), nullable=False)
    bot_user_id = Column(BigInteger())
    chat_id = Column(Integer())
    created_date = Column(Date, default=date.today)

    user_state = relationship("UserState", back_populates="user", uselist=False)
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    habit_complected_count = relationship("HabitComplected", back_populates="user", cascade="all, delete-orphan")
    reminder_jobs = relationship("SchedulerJobs", back_populates="user", cascade="all, delete-orphan")


    def __init__(self, nickname, age, phone, email, password, bot_user_id, created_date):
        """
        Инициализирует профиль с заданными значениями.

        Parameters:
            full_name (str): Полное имя пользователя.
            phone (str): Номер телефона пользователя.
            email (str): Адрес электронной почты пользователя.
            avatar (str): Ссылка на аватар пользователя.
        """
        self.nickname = nickname
        self.age = age
        self.phone = phone
        self.email = email
        self.password_hash = self.hash_password(password)
        self.bot_user_id = bot_user_id
        self.created_date = created_date

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    @property
    def is_valid_email(self):
        """
        Проверяет валидность адреса электронной почты.

        Returns:
            bool: True, если адрес электронной почты валиден, иначе False.
        """
        if self.email is None:
            return False
        regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(regex, self.email) is not None


class UserState(Base):
    """
    Представляет состояние пользователя в системе.

    Атрибуты:
        id (int): Уникальный идентификатор состояния пользователя.
        user_id (int): Идентификатор пользователя, связанного с этим состоянием.
        state (str): Текущее состояние пользователя.
        data (str): Дополнительные данные, связанные с состоянием пользователя.

    Взаимосвязи:
        user (User): Пользователь, связанный с этим состоянием.
    """

    __tablename__ = "user_state"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    state = Column(String, nullable=True)
    data = Column(String, nullable=True)
    user = relationship("User", back_populates="user_state")


class Habit(Base):
    """
    Представляет привычку, связанную с пользователем.

    Атрибуты:
        id (int): Уникальный идентификатор привычки.
        user_id (int): Идентификатор пользователя, владеющего этой привычкой.
        habit_name (str): Название привычки.
        duration (int): Продолжительность, на которую следует практиковать привычку.
        comments (str): Дополнительные комментарии о привычке.
        created_date (date): Дата создания привычки.
        reminder_time (str): Время, в которое должны отправляться напоминания о привычке.
        count_remained_day (int): Счетчик оставшихся дней для завершения привычки.

    Взаимосвязи:
        user (User): Пользователь, связанный с этой привычкой.
        habit_completed (HabitCompleted): Запись о завершенных привычках.
        reminder_jobs (SchedulerJobs): Запланированные задания для напоминаний, связанные с этой привычкой.
    """
    __tablename__ = "habit"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer(), ForeignKey("user.id"))
    habit_name = Column(String(50), nullable=False)
    duration = Column(Integer(), default=0)
    comments = Column(String(100))
    created_date = Column(Date, default=date.today)
    reminder_time = Column(String(20))
    count_remained_day = Column(Integer(), default=0)

    user = relationship("User", back_populates="habits")
    habit_complected = relationship("HabitComplected", back_populates="habit", uselist=False)
    reminder_jobs = relationship("SchedulerJobs", back_populates="habit", cascade="all, delete-orphan")


    def __init__(self, user_id, habit_name, duration, comments, created_date, reminder_time):
        self.user_id = user_id
        self.habit_name = habit_name
        self.duration = duration
        self.comments = comments
        self.created_date = created_date
        self.reminder_time = reminder_time
        self.count_remained_day = 0

    def increment_remained_day(self):
        self.count_remained_day +=1


class SchedulerJobs(Base):
    """
    Представляет запланированное задание для отправки напоминаний.

    Атрибуты:
        id (int): Уникальный идентификатор запланированного задания.
        job_id (str): Идентификатор задания в планировщике.
        user_id (int): Идентификатор пользователя, связанного с этим заданием.
        habit_id (int): Идентификатор привычки, связанной с этим заданием.

    Взаимосвязи:
        user (User): Пользователь, связанный с этим запланированным заданием.
        habit (Habit): Привычка, связанная с этим запланированным заданием.
    """
    __tablename__ = "scheduler_jobs"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"))
    habit_id = Column(Integer, ForeignKey("habit.id"))

    user = relationship("User", back_populates="reminder_jobs")
    habit = relationship("Habit", back_populates="reminder_jobs")



class HabitComplected(Base):
    """
    Отслеживает статус завершения привычек для пользователей.

    Атрибуты:
        id (int): Уникальный идентификатор записи о завершенной привычке.
        user_id (int): Идентификатор пользователя, владеющего привычкой.
        habit_id (int): Идентификатор привычки, связанной с этой записью.
        count_habit_completed (int): Количество завершенных случаев привычки.
        count_habit_not_completed (int): Количество случаев привычки, не завершенных.
        created_date (date): Дата создания этой записи.

    Взаимосвязи:
        user (User): Пользователь, связанный с этой записью о завершении привычки.
        habit (Habit): Привычка, связанная с этой записью о завершении.
    """
    __tablename__ = "habit_complected"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    habit_id = Column(Integer, ForeignKey("habit.id"))
    count_habit_complected = Column(Integer, default=0)
    count_habit_not_complected = Column(Integer, default=0)
    created_date = Column(Date, default=date.today)

    user = relationship("User", back_populates="habit_complected_count")
    habit = relationship("Habit", back_populates="habit_complected")

    def __init__(self, created_date, user_id, habit_id):
        self.created_date = created_date
        self.user_id = user_id
        self.habit_id = habit_id
        self.count_habit_complected = 0
        self.count_habit_not_complected = 0
        # self.remained_day = 0

    def increment_count_complected(self):
        self.count_habit_complected += 1

    def increment_count_not_complected(self):
        self.count_habit_not_complected += 1

    def increment_remained_day(self):
        self.remained_day +=1



class MessageControl(Base):
    """
    Представляет контрольную запись для сообщений, отправленных в чате.

    Атрибуты:
       id (int): Уникальный идентификатор записи контроля сообщения.
       chat_id (int): Идентификатор чата, в котором было отправлено сообщение.
       message_id (int): Идентификатор отправленного сообщения.
       user_id (int): Идентификатор пользователя, отправившего сообщение.
       timestamp (datetime): Время, когда было отправлено сообщение.

    Инициализация:
       Инициализирует запись контроля сообщения с chat_id, message_id и user_id.
    """
    __tablename__ = "message_control"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    def __init__(self, chat_id, message_id, user_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.user_id = user_id