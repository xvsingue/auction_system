from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BidViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'bids', BidViewSet, basename='bids')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]