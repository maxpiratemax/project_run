from django.contrib.auth.models import User
from rest_framework import serializers

from app_run.services.geo import (
    LATITUDE_MAX,
    LATITUDE_MIN,
    LONGITUDE_MAX,
    LONGITUDE_MIN,
)
from .models import Run, Challenge, AthleteInfo, Position, CollectibleItem, Subscribe


class AthleteDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name']


class RunSerializer(serializers.ModelSerializer):
    athlete_data = AthleteDataSerializer(source='athlete', read_only=True)

    class Meta:
        model = Run
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    runs_finished = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'date_joined', 'username', 'last_name', 'first_name', 'type', 'runs_finished']

    def get_type(self, obj):
        if obj.is_staff:
            return 'coach'

        return 'athlete'


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['id', 'full_name', 'athlete']


class AthleteInfoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = AthleteInfo
        fields = ['user_id', 'weight', 'goals']


class PositionSerializer(serializers.ModelSerializer):
    date_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%f')

    class Meta:
        model = Position
        fields = ['id', 'run', 'latitude', 'longitude', 'date_time', 'created_at', 'speed', 'distance']

    def validate_run(self, value):
        if value.status != Run.Status.IN_PROGRESS:
            raise serializers.ValidationError("Забег должен быть в статусе 'in_progress'.")
        return value

    def validate_latitude(self, value):
        if not (LATITUDE_MIN <= value <= LATITUDE_MAX):
            raise serializers.ValidationError(
                f"Широта должна быть в диапазоне [{LATITUDE_MIN}, {LATITUDE_MAX}]."
            )
        return value

    def validate_longitude(self, value):
        if not (LONGITUDE_MIN <= value <= LONGITUDE_MAX):
            raise serializers.ValidationError(
                f"Долгота должна быть в диапазоне [{LONGITUDE_MIN}, {LONGITUDE_MAX}]."
            )
        return value


class CollectibleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectibleItem
        fields = ['id', 'name', 'uid', 'latitude', 'longitude', 'picture', 'value']

    def validate_latitude(self, value):
        if not (LATITUDE_MIN <= value <= LATITUDE_MAX):
            raise serializers.ValidationError(
                f"Широта должна быть в диапазоне [{LATITUDE_MIN}, {LATITUDE_MAX}]."
            )
        return value

    def validate_longitude(self, value):
        if not (LONGITUDE_MIN <= value <= LONGITUDE_MAX):
            raise serializers.ValidationError(
                f"Долгота должна быть в диапазоне [{LONGITUDE_MIN}, {LONGITUDE_MAX}]."
            )
        return value


class UserDetailSerializer(UserSerializer):
    items = CollectibleItemSerializer(
        many=True,
        read_only=True,
        source='collectible_items',
    )

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ['items']


class CoachDetailSerializer(UserSerializer):
    items = CollectibleItemSerializer(
        many=True,
        read_only=True,
        source='collectible_items',
    )
    athletes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ['items', 'athletes']

    def get_athletes(self, obj):
        return list(
            Subscribe.objects.filter(coach=obj)
            .values_list('athlete_id', flat=True)
        )


class AthleteDetailSerializer(UserSerializer):
    items = CollectibleItemSerializer(
        many=True,
        read_only=True,
        source='collectible_items',
    )
    coach = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ['items', 'coach']

    def get_coach(self, obj):
        subscription = (
            Subscribe.objects.filter(athlete=obj)
            .select_related('coach')
            .first()
        )
        if subscription is None:
            return None
        return subscription.coach_id


class SubscribeSerializer(serializers.Serializer):
    athlete = serializers.IntegerField()

    def validate_athlete(self, value):
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Атлет не найден")
        return value
