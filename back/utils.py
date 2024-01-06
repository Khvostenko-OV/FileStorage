import json
import re

from django.http import JsonResponse, HttpRequest, QueryDict
from django.http.multipartparser import MultiPartParser

from back.settings import ERROR_NO_AUTH, ERROR_METHOD, ERROR_NO_PERMIT


def auth_required(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated:
            return func(request, *args, **kwargs)
        else:
            return JsonResponse(ERROR_NO_AUTH)
    return wrap


def admin_only(func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return func(request, *args, **kwargs)
        else:
            return JsonResponse(ERROR_NO_PERMIT)
    return wrap


def allowed_methods(*methods):
    def decor(func):
        def wrap(request, *args, **kwargs):
            if request.method in methods:
                return func(request, *args, **kwargs)
            else:
                return JsonResponse(ERROR_METHOD)
        return wrap
    return decor


def parse_body(request: HttpRequest) -> dict:

    if request.content_type.startswith("multipart"):
        data, m_dict = MultiPartParser(request.META, request, request.upload_handlers).parse()
        return data

    if request.content_type.startswith("application/json"):
        return json.loads(request.body.decode('utf-8'))

    return QueryDict(request.body)


def valid_username(name: str) -> bool:
    if len(name) < 4 or len(name) > 20:
        return False
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", name))


def valid_password(psw: str) -> bool:
    if len(psw) < 6:
        return False
    return bool(re.search(r"[A-Z]", psw)) and bool(re.search(r"[!@#$%^&*()_+={}[\]:;<>,.?|/~`']", psw))


def valid_filename(name: str) -> bool:
    return bool(re.match(r"^[^\n\\/:*?\"<>|]+(?<!\.)$", name))
