from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from app_run.services.geo import latitude_validators, longitude_validators


# Create your models here.
class Challenge(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Название челленджа")
    athlete = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Атлет",
        related_name='challenges'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Челлендж"
        verbose_name_plural = "Челленджи"

    def __str__(self):
        return f"{self.full_name} — {self.athlete}"


class Run(models.Model):
    class Status(models.TextChoices):
        INIT = 'init'
        IN_PROGRESS = 'in_progress'
        FINISHED = 'finished'

    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(verbose_name="Комментарий")
    athlete = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Атлет",  related_name='runs')

    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.INIT,
        verbose_name="Статус забега"
    )
    distance = models.FloatField(default=0, verbose_name="Дистанция, км")
    run_time_seconds = models.IntegerField(default=0, verbose_name="Время забега, сек")

    class Meta:
        verbose_name = "Забег"
        verbose_name_plural = "Забеги"

    def __str__(self):
        return f"{self.athlete} — {self.comment[:40]}"


class AthleteInfo(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="athlete_info",
        verbose_name="Атлет",
    )
    weight = models.IntegerField(default=1)
    goals = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Информация об атлете"
        verbose_name_plural = "Информация об атлетах"

    def __str__(self):
        return f"AthleteInfo for user_id={self.user_id}"


class Position(models.Model):
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name='positions',
        verbose_name="Забег"
    )
    latitude = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        verbose_name="Широта",
        validators=latitude_validators(),
    )
    longitude = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        verbose_name="Долгота",
        validators=longitude_validators(),
    )
    date_time = models.DateTimeField(default=timezone.now, verbose_name="Дата и время с трекера")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"

    def __str__(self):
        return f"Position {self.id} for run {self.run_id}"


class CollectibleItem(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    uid = models.CharField(max_length=255, verbose_name="UID")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    picture = models.URLField(verbose_name="Изображение")
    value = models.IntegerField(verbose_name="Ценность")
    athletes = models.ManyToManyField(
        User,
        related_name='collectible_items',
        blank=True,
        verbose_name="Атлеты, собравшие предмет",
    )

    class Meta:
        verbose_name = "Коллекционный предмет"
        verbose_name_plural = "Коллекционные предметы"

    def __str__(self):
        return f"{self.name} ({self.uid})"
