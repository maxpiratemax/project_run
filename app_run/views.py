from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as drf_status

from app_run.models import Run
from app_run.serializers import RunSerializer, UserSerializer


@api_view(['GET'])
def company_details(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.SLOGAN,
        'contacts': settings.CONTACTS,
    }
    return Response(details)


class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.select_related('athlete').all()
    serializer_class = RunSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name']

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

        return Response(
            {
                "detail": "Забег завершён.",
                "run_id": run.id,
                "status": run.status,
            },
            status=drf_status.HTTP_200_OK,
        )
