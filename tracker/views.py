from django.db.models import Q
from rest_framework import viewsets, permissions
from .models import Habit
from .serializers import HabitSerializer


class IsOwnerOrPublic(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPublic]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Habit.objects.filter(
                Q(user=user) | Q(is_public=True)
            ).distinct()
        return Habit.objects.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
