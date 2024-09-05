from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'expenses', views.ExpenseViewSet)
router.register(r'participants', views.ParticipantViewSet)
router.register(r'transactions', views.TransactionViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:user_id>/balances/', views.user_balances, name='user_balances'),
    path('users/<int:user_id>/expenses/', views.user_expenses, name='user_expenses'),
    path('simplify-expenses/', views.simplify_expenses, name='simplify_expenses')
]