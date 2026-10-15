from django.urls import path, include
from django.http import JsonResponse
from portal import views, api

api_patterns = [
    path('', views.dashboard, name='dashboard'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('outils/', views.tools_view, name='tools'),
    path('missions/', views.missions, name='missions'),
    path('missions/nouvelle/', views.mission_create, name='mission_create'),
    path('missions/<int:pk>/', views.mission_detail, name='mission'),
    path('missions/<int:pk>/test/', views.record_test, name='record_test'),
    path('missions/<int:pk>/statut/', views.mission_status, name='mission_status'),
    path('tests/<int:pk>/suivi/', views.update_finding, name='update_finding'),
    path('missions/<int:pk>/rapport/', views.report, name='report'),
    path('journal/', views.journal, name='journal'),
    path('journal/export/', views.export_journal, name='export_journal'),
    path('utilisateurs/', views.users, name='users'),
    path('utilisateurs/<int:pk>/acces/', views.user_access, name='user_access'),
    path('conformite/', views.compliance, name='compliance'),
]

urlpatterns = [path('api/session/', api.session, name='session'), path('api/', include(api_patterns))]
urlpatterns += [path(str(route.pattern), api.shell) for route in api_patterns if route.name not in ('logout', 'mission_status', 'report', 'export_journal')]
urlpatterns += [path('api/<path:unknown>', lambda request, **kw: JsonResponse({'error': 'Endpoint inconnu.'}, status=404))]
