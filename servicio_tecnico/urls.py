
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView # <--- ¡ESTA ES LA LÍNEA QUE FALTABA!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirige la raíz (/) a /servicios/
    path('', RedirectView.as_view(url='servicios/'), name='home'), 

    # Incluimos las URLs de la aplicación gestion_servicios
    path('servicios/', include('gestion_servicios.urls')),
    
    # Rutas de autenticación (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')), 
]