from django.urls import path

from users.views import user_login, user_logout, user_get_change_del, user_create, user_list, user_action

urlpatterns = [
    path("login/", user_login, name="login", ),
    path("logout/", user_logout, name="logout"),
    path("user/", user_get_change_del, name="user_gcd"),
    path("user/new/", user_create, name="user_create"),
    path("user/list/", user_list, name="user_list"),  # Admin only
    path("user/manage/<str:username>/", user_action, name="user_action"),  # Admin only
]
