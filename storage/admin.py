from django.contrib import admin

from storage.models import StoredFile, Link


@admin.register(StoredFile)
class FileAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "owner", "size", "downloads", "created_at"]
    list_display_links = ("name",)


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ["pk", "to_file", "href", "created_at", "expire_at"]
    list_display_links = ("href",)
