from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout

from back.settings import logger, OK_200, ERROR_SOME, ERROR_BAD_AUTH, ERROR_INVALID_LOGIN, ERROR_INVALID_PSW
from back.settings import ERROR_NEED_LOGIN, ERROR_EXIST_LOGIN, ERROR_NEED_PSW, ERROR_BAD_PSW
from back.utils import auth_required, allowed_methods, admin_only, parse_body, valid_username, valid_password
from users.models import User


@allowed_methods("POST")
def user_login(request):
    """ Authenticate and login """

    data = parse_body(request)
    username = data.get("username")
    password = data.get("password")
    if not username:
        logger.error("Action: authentication | No login")
        return JsonResponse(ERROR_NEED_LOGIN)
    if not password:
        logger.error("Action: authentication | No password")
        return JsonResponse(ERROR_NEED_PSW)

    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        # Delete expired user's links
        [[l.delete() for l in f.links.all() if l.expired] for f in user.files.all()]
        logger.info(f"User: {user} | Action: logged in")
        return JsonResponse({"ok": 200, "user": user.serializer})

    logger.error(f"Action: authentication | Bad pair login '{username}' / password '{password}'")
    return JsonResponse(ERROR_BAD_AUTH)


@allowed_methods("POST")
def user_logout(request):
    """ Logout and close user session"""
    name = request.user.username
    logout(request)
    logger.info(f"User: {name} | Action: logged out")
    return JsonResponse(OK_200)


@auth_required
@allowed_methods("GET", "PATCH", "DELETE")
def user_get_change_del(request):
    """
        GET - Get current user's info
        PATCH - Change current user
        DELETE - Delete current user and all his files and links
    """

#  Get current user's info
    if request.method == "GET":
        return JsonResponse({"ok": 200, "user": request.user.serializer})

#  Change current user
    if request.method == "PATCH":

        data = parse_body(request)
        user = request.user
        username = data.get("username", user.username)
        if not valid_username(username):
            logger.error(f"User: {user} | Action: change username | Invalid login {username}")
            return JsonResponse(ERROR_INVALID_LOGIN)
        if username != user.username and User.objects.filter(username=username).exists():
            logger.error(f"User: {user} | Action: change username | Login already exists")
            return JsonResponse(ERROR_EXIST_LOGIN)

        password = data.get("password")
        if password:
            old_password = data.get("old_password")
            if not old_password:
                logger.error(f"User: {user} | Action: change password | Password needed")
                return JsonResponse(ERROR_NEED_PSW)
            if not user.check_password(old_password):
                logger.error(f"User: {user} | Action: change password | Bad password")
                return JsonResponse(ERROR_BAD_PSW)
            if not valid_password(password):
                logger.error(f"User: {user} | Action: change password | Invalid password {password}")
                return JsonResponse(ERROR_INVALID_PSW)
            user.set_password(password)
            user.save()
            user = authenticate(request, username=user.username, password=password)
            login(request, user)

        user.username = username
        user.email = data.get("email", user.email)
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.save()
        logger.info(f"User: {user} | Action: user changed")
        return JsonResponse({"ok": 200, "user": request.user.serializer})

#  Delete current user and all his files and links
    if request.method == "DELETE":

        data = parse_body(request)
        user = request.user
        password = data.get("password")
        if not password:
            logger.error(f"User: {user} | Action: delete user | Password needed")
            return JsonResponse(ERROR_NEED_PSW)

        if not user.check_password(password):
            logger.error(f"User: {user} | Action: delete user | Bad password")
            return JsonResponse(ERROR_BAD_PSW)

        name = user.username
        files_count = user.files_count
        logout(request)
        user.delete()
        logger.info(f"User: {name} | Action: user deleted, {files_count} files deleted")
        return JsonResponse(OK_200)

    return JsonResponse(ERROR_SOME)


@allowed_methods("POST")
def user_create(request):
    """ Create new user """

    data = parse_body(request)
    username = data.get("username")
    password = data.get("password")

    if not username:
        logger.error("Action: create new user | No login")
        return JsonResponse(ERROR_NEED_LOGIN)
    if not valid_username(username):
        logger.error(f"Action: create new user | Invalid login {username}")
        return JsonResponse(ERROR_INVALID_LOGIN)
    if User.objects.filter(username=username):
        logger.error("Action: create new user | Login already exists")
        return JsonResponse(ERROR_EXIST_LOGIN)

    if not password:
        logger.error("Action: create new user | No password")
        return JsonResponse(ERROR_NEED_PSW)
    if not valid_password(password):
        logger.error(f"Action: create new user | Invalid password {password}")
        return JsonResponse(ERROR_INVALID_PSW)

    user = User.objects.create_user(username, data.get("email", ""), password)
    user.first_name = data.get("first_name", "")
    user.last_name = data.get("last_name", "")
    user.save()

    logger.info(f"User: {user} | Action: user created")
    return JsonResponse({"ok": 201, "user": user.serializer})


@admin_only
@allowed_methods("GET")
def user_list(request):
    """ Get list of users """
    return JsonResponse({"ok": 200, "users": [u.seralizer for u in User.objects.all()]})


@admin_only
@allowed_methods("GET", "PATCH", "DELETE")
def user_action(request, username: str):
    """
        url param: username
        GET - Get user's info
        PATCH - Change user
        DELETE - Delete user and all his files and links
    """

    user = User.objects.filter(username=username).first()
    if not user:
        return JsonResponse({"error": 404, "error_msg": f"User '{username}' not found"})

#  Get user's info
    if request.method == "GET":
        return JsonResponse({
            "ok": 200,
            "user": user.serializer,
            "files": [f.serializer for f in user.files.all()],
        })

#  Change user
    if request.method == "PATCH":
        data = parse_body(request)
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.save()
        logger.info(f"User: {request.user} | Action: change user {user.pk}: {user.username}")
        return JsonResponse({"ok": 200, "user": user.serializer})

#  Delete user and all his files and links
    if request.method == "DELETE":
        pk = user.pk
        files_count = user.files_count
        user.delete()
        logger.info(f"User: {request.user} | Action: delete user {pk}: {username}, {files_count} files deleted")
        return JsonResponse(OK_200)
