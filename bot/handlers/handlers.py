from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

class LoginStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

class TaskCreationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_text = State()

# Create keyboards for main menu
def get_main_menu(is_authenticated: bool = False) -> ReplyKeyboardMarkup:
    if is_authenticated:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Получить таски'), KeyboardButton(text='Создать таск')],
                [KeyboardButton(text='Выйти')]
            ],
            resize_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Зарегистрироваться'),
                KeyboardButton(text='Логин'),
            ],
        ],
        resize_keyboard=True
    )

# Create keyboard for skipping text_of_task
def get_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Пропустить')]
        ],
        resize_keyboard=True
    )

# Start command handler
@router.message(CommandStart())
async def command_start(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    is_authenticated = 'access_token' in user_data
    logger.info(f"Start command: is_authenticated={is_authenticated}, user_data={user_data}")
    await message.answer(
        'Hi! What do you want?',
        reply_markup=get_main_menu(is_authenticated),
    )
    if not is_authenticated:
        await state.clear()

# Registration button handler
@router.message(F.text == 'Зарегистрироваться')
async def start_registration(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if 'access_token' in user_data:
        await message.answer(
            "You are already registered and logged in!",
            reply_markup=get_main_menu(is_authenticated=True)
        )
        return
    await message.answer(
        "Please enter your email:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.waiting_for_email)

# Handle email input for registration
@router.message(RegistrationStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext) -> None:
    if '@' not in message.text:
        await message.answer("Please enter a valid email address:")
        return
    await state.update_data(email=message.text)
    await message.answer("Please enter your password:")
    await state.set_state(RegistrationStates.waiting_for_password)

# Handle password input for registration
@router.message(RegistrationStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext) -> None:
    await state.update_data(password=message.text)
    user_data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/auth/register',
                json={
                    'email': user_data['email'],
                    'password': user_data['password'],
                    'is_active': True,
                    'is_superuser': False,
                    'is_verified': False
                }
            ) as response:
                logger.info(f"Register response: {response.status} {await response.text()}")
                if response.status == 201:
                    response_data = await response.json()
                    token = response_data.get('access_token')
                    if token:
                        await state.update_data(access_token=token)
                        logger.info(f"Stored token: {token}")
                    await message.answer(
                        f"Registration successful!\nEmail: {user_data['email']}",
                        reply_markup=get_main_menu(is_authenticated=True)
                    )
                else:
                    try:
                        error_data = await response.json()
                        await message.answer(
                            f"Registration failed: {error_data.get('detail', 'Unknown error')}",
                            reply_markup=get_main_menu()
                        )
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        await message.answer(
                            f"Registration failed: Server returned non-JSON response: {error_text}",
                            reply_markup=get_main_menu()
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Register error: {str(e)}")
            await message.answer(
                f"Error connecting to server: {str(e)}",
                reply_markup=get_main_menu()
            )
    await state.set_state(None)

# Login button handler
@router.message(F.text == 'Логин')
async def start_login(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if 'access_token' in user_data:
        await message.answer(
            "You are already logged in!",
            reply_markup=get_main_menu(is_authenticated=True)
        )
        return
    await message.answer(
        "Please enter your email:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(LoginStates.waiting_for_email)

# Handle login email input
@router.message(LoginStates.waiting_for_email)
async def process_login_email(message: types.Message, state: FSMContext) -> None:
    if '@' not in message.text:
        await message.answer("Please enter a valid email address:")
        return
    await state.update_data(email=message.text)
    await message.answer("Please enter your password:")
    await state.set_state(LoginStates.waiting_for_password)

# Handle login password input
@router.message(LoginStates.waiting_for_password)
async def process_login_password(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/auth/jwt/login',
                data={
                    'username': user_data['email'],
                    'password': message.text
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                logger.info(f"Login response: {response.status} {await response.text()}")
                if response.status == 200:
                    response_data = await response.json()
                    token = response_data.get('access_token')
                    if token:
                        await state.update_data(access_token=token)
                        logger.info(f"Stored token: {token}")
                    await message.answer(
                        f"Login successful!\nEmail: {user_data['email']}\nYou can now get your tasks!",
                        reply_markup=get_main_menu(is_authenticated=True)
                    )
                else:
                    try:
                        error_data = await response.json()
                        await message.answer(
                            f"Login failed: {error_data.get('detail', 'Unknown error')}",
                            reply_markup=get_main_menu()
                        )
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        await message.answer(
                            f"Login failed: Server returned non-JSON response: {error_text}",
                            reply_markup=get_main_menu()
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Login error: {str(e)}")
            await message.answer(
                f"Error connecting to server: {str(e)}",
                reply_markup=get_main_menu()
            )
    await state.set_state(None)

# Logout handler
@router.message(F.text == 'Выйти')
async def logout(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "You have been logged out.",
        reply_markup=get_main_menu(is_authenticated=False)
    )

# Handle "Get Tasks" button
@router.message(F.text == 'Получить таски')
async def get_tasks(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if 'access_token' not in user_data:
        await message.answer(
            "Please log in or register first!",
            reply_markup=get_main_menu(is_authenticated=False)
        )
        return
    logger.info(f"Get tasks with token: {user_data['access_token']}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                'http://localhost:8000/tasks/',
                headers={'Authorization': f'Bearer {user_data["access_token"]}'}
            ) as response:
                logger.info(f"Get tasks response: {response.status} {await response.text()}")
                if response.status == 200:
                    tasks = await response.json()
                    if tasks:
                        tasks_list = "\n".join([
                            f"Task {i + 1}:\nname: {task['name']}\ntext: {task.get('text_of_task', 'None')}\ncreated_at: {task['created_at']}"
                            for i, task in enumerate(tasks)
                        ])
                        await message.answer(
                            f"Your tasks:\n{tasks_list}",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
                    else:
                        await message.answer(
                            "You have no tasks.",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
                elif response.status == 401:
                    await state.clear()
                    await message.answer(
                        "Your session has expired. Please log in again.",
                        reply_markup=get_main_menu(is_authenticated=False)
                    )
                else:
                    try:
                        error_data = await response.json()
                        await message.answer(
                            f"Failed to fetch tasks: {error_data.get('detail', 'Unknown error')}",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        await message.answer(
                            f"Failed to fetch tasks: Server returned non-JSON response: {error_text}",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Get tasks error: {str(e)}")
            await message.answer(
                f"Error connecting to server: {str(e)}",
                reply_markup=get_main_menu(is_authenticated=True)
            )

# Handle "Create Task" button
@router.message(F.text == 'Создать таск')
async def start_task_creation(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if 'access_token' not in user_data:
        await message.answer(
            "Please log in or register first!",
            reply_markup=get_main_menu(is_authenticated=False)
        )
        return
    await message.answer(
        "Please enter the task name:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TaskCreationStates.waiting_for_name)

# Handle task name input
@router.message(TaskCreationStates.waiting_for_name)
async def process_task_name(message: types.Message, state: FSMContext) -> None:
    if not message.text.strip():
        await message.answer("Task name cannot be empty. Please enter a valid name:")
        return
    await state.update_data(task_name=message.text.strip())
    await message.answer(
        "Please enter the task description (or press 'Пропустить' to leave it empty):",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(TaskCreationStates.waiting_for_text)

# Handle task text input or skip
@router.message(TaskCreationStates.waiting_for_text)
async def process_task_text(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    task_text = None if message.text == 'Пропустить' else message.text.strip()
    logger.info(f"Creating task with token: {user_data['access_token']}, name: {user_data['task_name']}, text: {task_text}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/tasks/',
                json={
                    'name': user_data['task_name'],
                    'text_of_task': task_text
                },
                headers={'Authorization': f'Bearer {user_data["access_token"]}'}
            ) as response:
                logger.info(f"Create task response: {response.status} {await response.text()}")
                if response.status == 201:
                    response_data = await response.json()
                    await message.answer(
                        f"Task created successfully!\nname: {response_data['name']}\ntext: {response_data.get('text_of_task', 'None')}\ncreated_at: {response_data['created_at']}",
                        reply_markup=get_main_menu(is_authenticated=True)
                    )
                elif response.status == 401:
                    await state.clear()
                    await message.answer(
                        "Your session has expired. Please log in again.",
                        reply_markup=get_main_menu(is_authenticated=False)
                    )
                else:
                    try:
                        error_data = await response.json()
                        await message.answer(
                            f"Failed to create task: {error_data.get('detail', 'Unknown error')}",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        await message.answer(
                            f"Failed to create task: Server returned non-JSON response: {error_text}",
                            reply_markup=get_main_menu(is_authenticated=True)
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Create task error: {str(e)}")
            await message.answer(
                f"Error connecting to server: {str(e)}",
                reply_markup=get_main_menu(is_authenticated=True)
            )
    await state.set_state(None)  # Clear only task creation state, keep access_token