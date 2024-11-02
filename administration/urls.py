from django.urls import include, path

app_name = 'administration'

urlpatterns = [
    path('v1/', include('administration.api.v1.urls')),
]