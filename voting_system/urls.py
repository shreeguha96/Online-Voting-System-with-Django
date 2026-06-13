from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Online Voting System API",
        default_version='v1',
        description="""
# Online Voting System API

A complete REST API for managing elections, candidates, voters, and votes.

## Features
- **Elections** – Create, activate, close elections
- **Candidates** – Manage candidates per election
- **Voters** – Register and manage voter eligibility
- **Votes** – Cast and audit votes
- **Results** – View live/final election results
- **Audit Logs** – Full action trail
- **Dashboard** – System statistics

## Quick Start
1. Register voters via `POST /api/voters/`
2. Create an election via `POST /api/elections/`
3. Add candidates via `POST /api/elections/{id}/candidates/`
4. Activate election via `POST /api/elections/{id}/activate/`
5. Cast votes via `POST /api/votes/cast/`
6. View results via `GET /api/elections/{id}/results/`
        """,
        contact=openapi.Contact(email="admin@votingsystem.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('elections.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
