from django.contrib import admin

from storage.models import StoredFile
from users.models import User


class FileInline(admin.TabularInline):
    model = StoredFile
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["pk", "username", "first_name", "last_name", "files_count", "total_size", "is_superuser", "uuid"]
    list_display_links = ("username",)
    fields = ["username", ("first_name", "last_name"), "email", "is_superuser"]
    inlines = (FileInline,)
