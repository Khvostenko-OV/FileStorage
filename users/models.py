import os
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser

from back.settings import STORAGE_DIR


class User(AbstractUser):
    """
      Inherited fields:
        username: str
        password: hash
        email: str
        first_name: str
        last_name: str
        is_superuser: bool
    """

    uuid = models.UUIDField("UUID", default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("Created at", auto_now_add=True, null=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True, null=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["pk"]

    def __str__(self):
        return self.username

    @property
    def dir(self):
        return os.path.join(STORAGE_DIR, str(self.uuid))

    @property
    def files_count(self):
        return self.files.all().count()

    @property
    def total_size(self):
        return sum([f.size for f in self.files.all()])

    @property
    def serializer(self):
        return {
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_admin": self.is_superuser,
        }

    def delete(self, using=None, keep_parents=False):
        [f.file.delete() for f in self.files.all()]
        if os.path.exists(self.dir):
            os.rmdir(self.dir)
        return super().delete()
