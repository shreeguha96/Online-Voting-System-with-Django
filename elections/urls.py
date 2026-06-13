from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'elections', views.ElectionViewSet, basename='election')
router.register(r'candidates', views.CandidateViewSet, basename='candidate')
router.register(r'voters', views.VoterViewSet, basename='voter')
router.register(r'votes', views.VoteViewSet, basename='vote')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')
router.register(r'dashboard', views.DashboardView, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
