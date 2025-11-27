from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinanceViewSet
from . import views

router = DefaultRouter()
router.register(r'', FinanceViewSet, basename='finance')
urlpatterns = [
    path('', include(router.urls)),
]
