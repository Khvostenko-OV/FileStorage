from django.urls import path

from storage.views import file_list, file_get_change_del, file_upload, file_download, link_create, link_download

urlpatterns = [
    path("storage/", file_list, name="file_list"),
    path("storage/upload/", file_upload, name="file_upload"),
    path("storage/file/<int:pk>/download/", file_download, name="file_download"),
    path("storage/file/<int:pk>/", file_get_change_del, name="file_gcd"),
    path("storage/file/link/", link_create, name="link_create"),
    path("storage/get/", link_download, name="link_download"),
]
