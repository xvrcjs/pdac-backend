from django.urls import include, path

app_name = 'security'

urlpatterns = [
    path('v1/', include('security.api.v1.urls')),
]