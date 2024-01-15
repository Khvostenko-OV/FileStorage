import os
import secrets
from datetime import datetime, timezone

from django.db import models

from back.settings import STORAGE_DIR, BASE_URL
from back.utils import valid_filename
from users.models import User


def owner_file_path(instance, filename):
    return f"{instance.owner.uuid}/{filename}"


def generate_href():
    return secrets.token_urlsafe(12)


class StoredFile(models.Model):
    """ Files in storage """

    file = models.FileField("File", upload_to=owner_file_path, max_length=256)
    name = models.CharField("Name", max_length=512, default="", null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files", verbose_name="Owner")
    description = models.CharField("Description", max_length=512, default="")
    downloads = models.IntegerField("Downloads", default=0)
    created_at = models.DateTimeField("Created at", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True, null=True)

    class Meta:
        verbose_name = "Stored File"
        verbose_name_plural = "Stored Files"
        ordering = ["name"]

    @property
    def dir(self):
        return self.file.name.split("/")[0]

    @property
    def exists(self):
        return os.path.exists(self.file.path)

    @property
    def size(self):
        return self.file.size if self.exists else -1

    def __str__(self):
        return self.name

    @property
    def serializer(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "downloads": self.downloads,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }

    def rename(self, new_name="") -> str:

        if new_name == self.name:
            return ""

        if not valid_filename(new_name):
            return f"Invalid filename - '{new_name}'"

        if self.owner.files.filter(name=new_name).exists():
            return f"File '{new_name}' already exists"

        if os.path.exists(self.file.path):
            new_path = os.path.join(STORAGE_DIR, self.dir, new_name)
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(self.file.path, new_path)

        self.file.name = f"{self.dir}/{new_name}"
        self.name = new_name
        self.save()
        return ""


class Link(models.Model):
    """ Links for downloading files """

    to_file = models.ForeignKey(StoredFile, on_delete=models.CASCADE, related_name="links", verbose_name="To file")
    href = models.CharField("Href", max_length=16, default=generate_href, unique=True, editable=False)
    created_at = models.DateTimeField("Created at", auto_now_add=True, null=True)
    expire_at = models.DateTimeField("Expire at", null=True)

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"
        ordering = ["pk"]

    def __str__(self):
        return f"{BASE_URL}storage/get/?link={self.href}"

    @property
    def expired(self):
        return self.expire_at and self.expire_at < datetime.now(timezone.utc)

    @property
    def serializer(self):
        return {
            "href": str(self),
            "file_name": self.to_file.name,
            "file_size": self.to_file.file.size,
            "expire_at": str(self.expire_at) if self.expire_at else "",
        }
