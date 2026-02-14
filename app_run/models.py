from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Run(models.Model):
    class Status(models.TextChoices):
        INIT = 'init'
        IN_PROGRESS = 'in_progress'
        FINISHED = 'finished'

    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(verbose_name="Комментарий")
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Атлет")

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.INIT,
        verbose_name="Статус забега"
    )

    class Meta:
        verbose_name = "Забег"
        verbose_name_plural = "Забеги"

    def __str__(self):
        return f"{self.athlete} — {self.comment[:40]}"
