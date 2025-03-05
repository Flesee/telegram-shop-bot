from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def redirect_to_admin(request):
    return redirect('admin:index')

urlpatterns = [
    path('', redirect_to_admin),  # Редирект с корневого URL на админку
    path('admin/', admin.site.urls),
]

# Добавляем URL-шаблоны для статических и медиа-файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 