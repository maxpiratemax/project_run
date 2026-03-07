from django.conf import settings
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as drf_status

from app_run.models import Run, Challenge, AthleteInfo
from app_run.serializers import (
    RunSerializer,
    UserSerializer,
    ChallengeSerializer,
    AthleteInfoSerializer,
)


@api_view(['GET'])
def company_details(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)


class RunPagination(PageNumberPagination):
    page_size_query_param = 'size'


class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related('athlete').all()
    serializer_class = RunSerializer
    pagination_class = RunPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at']
    filterset_fields = ['status', 'athlete']


class UserPagination(PageNumberPagination):
    page_size_query_param = 'size'


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['date_joined']

    def get_queryset(self):
        qs = self.queryset.filter(is_superuser=False)
        user_type = self.request.query_params.get('type', None)
        if user_type == "coach":
            qs = qs.filter(is_staff=True)
        elif user_type == "athlete":
            qs = qs.filter(is_staff=False)

        return qs


class RunStartAPIView(APIView):
    def post(self, request, run_id: int):
        try:
            run = Run.objects.get(pk=run_id)
        except Run.DoesNotExist:
            raise NotFound("Забег не найден")

        if run.status != Run.Status.INIT:
            return Response(
                {
                    "detail": "Нельзя стартовать забег: он уже стартовал или уже завершён.",
                    "run_id": run.id,
                    "current_status": run.status,
                },
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        run.status = Run.Status.IN_PROGRESS
        run.save(update_fields=["status"])

        return Response(
            {
                "detail": "Забег стартовал.",
                "run_id": run.id,
                "status": run.status,
            },
            status=drf_status.HTTP_200_OK,
        )


class RunStopAPIView(APIView):
    def post(self, request, run_id: int):
        try:
            run = Run.objects.get(pk=run_id)
        except Run.DoesNotExist:
            raise NotFound("Забег не найден")

        if run.status != Run.Status.IN_PROGRESS:
            return Response(
                {
                    "detail": "Нельзя завершить забег: он ещё не запущен или уже завершён.",
                    "run_id": run.id,
                    "current_status": run.status,
                },
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        run.status = Run.Status.FINISHED
        run.save(update_fields=["status"])

        finished_runs_count = Run.objects.filter(
            athlete=run.athlete,
            status=Run.Status.FINISHED
        ).count()

        QUANTITY_TO_ACHIEVEMENTS = 10

        if finished_runs_count == QUANTITY_TO_ACHIEVEMENTS:
            Challenge.objects.get_or_create(
                athlete=run.athlete,
                full_name=f"Сделай {QUANTITY_TO_ACHIEVEMENTS} Забегов!"
            )

        return Response(
            {
                "detail": "Забег завершён.",
                "run_id": run.id,
                "status": run.status,
            },
            status=drf_status.HTTP_200_OK,
        )


class ChallengePagination(PageNumberPagination):
    page_size_query_param = 'size'


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Challenge.objects.select_related('athlete').all()
    serializer_class = ChallengeSerializer
    pagination_class = ChallengePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['athlete']


class AthleteInfoAPIView(APIView):
    def _get_user_or_404(self, user_id: int) -> User:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise NotFound("Пользователь не найден")

    def get(self, request, user_id: int):
        user = self._get_user_or_404(user_id)
        athlete_info, _ = AthleteInfo.objects.get_or_create(user=user)
        serializer = AthleteInfoSerializer(athlete_info)
        return Response(serializer.data, status=drf_status.HTTP_200_OK)

    def put(self, request, user_id: int):
        user = self._get_user_or_404(user_id)
        athlete_info, _ = AthleteInfo.objects.get_or_create(user=user)

        if 'weight' in request.data:
            try:
                weight = int(request.data['weight'])
            except (TypeError, ValueError):
                return Response(
                    {"detail": "weight должен быть целым числом > 0 и < 900"},
                    status=drf_status.HTTP_400_BAD_REQUEST,
                )
            if not (0 < weight < 900):
                return Response(
                    {"detail": "weight должен быть > 0 и < 900"},
                    status=drf_status.HTTP_400_BAD_REQUEST,
                )
            athlete_info.weight = weight

        if 'goals' in request.data:
            athlete_info.goals = request.data['goals']

        athlete_info.save()
        serializer = AthleteInfoSerializer(athlete_info)
        return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
