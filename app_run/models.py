from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Run(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(verbose_name="Комментарий")
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Атлет")

    class Meta:
        verbose_name = "Забег"
        verbose_name_plural = "Забеги"

    def __str__(self):
        return f"{self.athlete} — {self.comment[:40]}"
