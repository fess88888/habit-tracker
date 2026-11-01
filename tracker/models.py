from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')

    action = models.CharField(max_length=200, verbose_name="Действие")
    time_of_day = models.TimeField(verbose_name="Время выполнения")
    location = models.CharField(max_length=200, blank=True, verbose_name="Место")

    is_pleasant = models.BooleanField(default=False, verbose_name="Приятная привычка")
    reward = models.TextField(blank=True, null=True, verbose_name="Вознаграждение")
    related_habit = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='related_habits',
        verbose_name="Связанная привычка (приятная)"
    )

    periodicity_days = models.PositiveIntegerField(default=1, verbose_name="Периодичность (дней)")
    execution_time_seconds = models.PositiveIntegerField(verbose_name="Время на выполнение (сек)")
    is_public = models.BooleanField(default=False, verbose_name="Публичность")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.reward and self.related_habit:
            raise ValidationError(_("Нельзя одновременно указать вознаграждение и связанную привычку."))

        if self.execution_time_seconds > 120:
            raise ValidationError(_("Время на выполнение привычки не должно превышать 120 секунд."))

        if self.is_pleasant:
            if self.reward:
                raise ValidationError(_("У приятной привычки не может быть вознаграждения."))
            if self.related_habit:
                raise ValidationError(_("У приятной привычки не может быть связанной привычки."))

        if self.related_habit and not self.related_habit.is_pleasant:
            raise ValidationError(_("Связанная привычка должна быть приятной."))

        if self.periodicity_days < 1 or self.periodicity_days > 7:
            raise ValidationError(_("Периодичность должна быть от 1 до 7 дней."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.action} ({self.user.username})"
