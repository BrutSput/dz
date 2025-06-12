from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth_views"])

templates = Jinja2Templates(directory="app/template")

@router.get("/", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "error": None, "success": None}
    )

@router.post("/", response_class=HTMLResponse)
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/auth/register',
                json={
                    'email': email,
                    'password': password,
                    'is_active': True,
                    'is_superuser': False,
                    'is_verified': False
                }
            ) as reg_response:
                logger.info(f"Register response: {reg_response.status} {await reg_response.text()}, headers: {reg_response.headers}")
                if reg_response.status == 201:
                    async with session.post(
                        'http://localhost:8000/auth/jwt/login',
                        data={
                            'username': email,
                            'password': password
                        },
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    ) as login_response:
                        logger.info(f"Auto-login response: {login_response.status} {await login_response.text()}, headers: {login_response.headers}")
                        if login_response.status == 200:
                            login_data = await login_response.json()
                            token = login_data.get('access_token')
                            if token:
                                response = RedirectResponse(url="/tasks", status_code=303)
                                response.set_cookie(key="access_token", value=token, httponly=True)
                                logger.info(f"Set cookie and redirecting to /tasks for {email}")
                                return response
                        try:
                            error_data = await login_response.json()
                            error_message = error_data.get('detail', 'Unknown error')
                        except aiohttp.ContentTypeError:
                            error_message = await login_response.text()
                        logger.error(f"Auto-login failed: {error_message}")
                        return templates.TemplateResponse(
                            "register.html",
                            {
                                "request": request,
                                "error": f"Auto-login failed: {error_message}",
                                "success": None
                            }
                        )
                else:
                    try:
                        error_data = await reg_response.json()
                        error_message = error_data.get('detail', 'Unknown error')
                    except aiohttp.ContentTypeError:
                        error_message = await reg_response.text()
                    logger.error(f"Registration failed: {error_message}")
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": f"Registration failed: {error_message}",
                            "success": None
                        }
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Registration error: {str(e)}")
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": f"Error connecting to server: {str(e)}",
                    "success": None
                }
            )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )

@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/auth/jwt/login',
                data={
                    'username': username,
                    'password': password
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                logger.info(f"Login response: {response.status} {await response.text()}, headers: {response.headers}")
                if response.status == 200:
                    response_data = await response.json()
                    token = response_data.get('access_token')
                    if token:
                        response = RedirectResponse(url="/tasks", status_code=303)
                        response.set_cookie(key="access_token", value=token, httponly=True)
                        logger.info(f"Set cookie and redirecting to /tasks for {username}")
                        return response
                    else:
                        logger.error("No access_token in login response")
                        return templates.TemplateResponse(
                            "login.html",
                            {
                                "request": request,
                                "error": "Login failed: No access token received",
                                "success": None
                            }
                        )
                else:
                    try:
                        error_data = await response.json()
                        error_message = error_data.get('detail', 'Unknown error')
                    except aiohttp.ContentTypeError:
                        error_message = await response.text()
                    logger.error(f"Login failed: {error_message}")
                    return templates.TemplateResponse(
                        "login.html",
                        {
                            "request": request,
                            "error": f"Login failed: {error_message}",
                            "success": None
                        }
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Login error: {str(e)}")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": f"Error connecting to server: {str(e)}",
                    "success": None
                }
            )

@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        logger.info("No token found, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                'http://localhost:8000/tasks/',
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                logger.info(f"Get tasks response: {response.status} {await response.text()}, headers: {response.headers}")
                if response.status == 200:
                    tasks = await response.json()
                    return templates.TemplateResponse(
                        "tasks.html",
                        {
                            "request": request,
                            "tasks": tasks,
                            "error": None,
                            "success": None
                        }
                    )
                elif response.status == 401:
                    logger.info("Unauthorized, clearing token and redirecting to /login")
                    response = RedirectResponse(url="/login", status_code=303)
                    response.delete_cookie("access_token")
                    return response
                else:
                    try:
                        error_data = await response.json()
                        error_message = error_data.get('detail', 'Unknown error')
                    except aiohttp.ContentTypeError:
                        error_message = await response.text()
                    logger.error(f"Failed to fetch tasks: {error_message}")
                    return templates.TemplateResponse(
                        "tasks.html",
                        {
                            "request": request,
                            "tasks": [],
                            "error": f"Failed to fetch tasks: {error_message}",
                            "success": None
                        }
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Get tasks error: {str(e)}")
            return templates.TemplateResponse(
                "tasks.html",
                {
                    "request": request,
                    "tasks": [],
                    "error": f"Error connecting to server: {str(e)}",
                    "success": None
                }
            )

@router.post("/tasks", response_class=HTMLResponse)
async def create_task(
    request: Request,
    name: str = Form(...),
    text_of_task: str = Form(None),
):
    token = request.cookies.get("access_token")
    if not token:
        logger.info("No token found, redirecting to /login")
        return RedirectResponse(url="/login", status_code=303)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:8000/tasks/',
                json={
                    'name': name,
                    'text_of_task': text_of_task
                },
                headers={'Authorization': f'Bearer {token}'}
            ) as response:
                logger.info(f"Create task response: {response.status} {await response.text()}, headers: {response.headers}")
                if response.status == 201:
                    return RedirectResponse(url="/tasks", status_code=303)
                elif response.status == 401:
                    logger.info("Unauthorized, clearing token and redirecting to /login")
                    response = RedirectResponse(url="/login", status_code=303)
                    response.delete_cookie("access_token")
                    return response
                else:
                    try:
                        error_data = await response.json()
                        error_message = error_data.get('detail', 'Unknown error')
                    except aiohttp.ContentTypeError:
                        error_message = await response.text()
                    logger.error(f"Failed to create task: {error_message}")
                    async with session.get(
                        'http://localhost:8000/tasks/',
                        headers={'Authorization': f'Bearer {token}'}
                    ) as tasks_response:
                        tasks = await tasks_response.json() if tasks_response.status == 200 else []
                    return templates.TemplateResponse(
                        "tasks.html",
                        {
                            "request": request,
                            "tasks": tasks,
                            "error": f"Failed to create task: {error_message}",
                            "success": None
                        }
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Create task error: {str(e)}")
            async with session.get(
                'http://localhost:8000/tasks/',
                headers={'Authorization': f'Bearer {token}'}
            ) as tasks_response:
                tasks = await tasks_response.json() if tasks_response.status == 200 else []
            return templates.TemplateResponse(
                "tasks.html",
                {
                    "request": request,
                    "tasks": tasks,
                    "error": f"Error connecting to server: {str(e)}",
                    "success": None
                }
            )

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    logger.info("Logging out, clearing token")
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response