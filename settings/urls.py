from django.contrib import admin
from django.urls import path, include, re_path

from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

import os.path

# Set admin page properties
title = settings.TITLE_FROM_ENVIRONMENT or 'Prueba'

title_w_stage = title if settings.ENV_STAGE.upper() == 'PROD' else (title + ' - ' + settings.ENV_STAGE.title())
admin.site.site_title = title_w_stage
admin.site.site_header = title_w_stage + \
    (' - UNVERSIONED' if settings.ENV_VERSION == 'UNVERSIONED' else f' - v{settings.ENV_VERSION}')


urlpatterns = [
    path('panel/', admin.site.urls),
    path('api/v1/', include('users.api.v1.urls', namespace='users')),
    path('api/v1/', include('security.api.v1.urls',namespace='security')),
    path('api/v1/', include('administration.api.v1.urls',namespace='administration')),
    path('api/v1/', include('claims.api.v1.urls', namespace='claims')),
    path('api/doc/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),
]


if settings.DEBUG:

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'myapp/images/favicon.ico'))
    ]
