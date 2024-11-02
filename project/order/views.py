from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet

from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(
    GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
):
    queryset = Order.objects.all().order_by("id")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
