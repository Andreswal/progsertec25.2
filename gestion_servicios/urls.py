
# gestion_servicios/urls.py
from django.urls import path
from . import views 

urlpatterns = [
    # Listado Principal (URL: /servicios/)
    path('', views.ReparacionListView.as_view(), name='lista_servicios'),
    
    # Creación (URL: /servicios/crear/)
    path('crear/', views.ReparacionCreateView.as_view(), name='crear_servicio'),
    
    # Modificación (URL: /servicios/4638/modificar/)
    path('<int:pk>/modificar/', views.ReparacionUpdateView.as_view(), name='modificar_servicio'),
    
    # Cierre de la orden y entrega
    # DESPUÉS: Usamos la función que definimos y decoramos con @require_POST.
    
    path('<int:pk>/cerrar/', views.cerrar_servicio_view, name='cerrar_servicio'),
    
    # (Opcional) path('<int:pk>/imprimir/', views.ReparacionImprimirPDFView.as_view(), name='imprimir_servicio'),
    # URL para la API de búsqueda AJAX/JSON (Nueva línea)
    path('api/buscar_cliente/', views.buscar_cliente_por_clave, name='api_buscar_cliente'),
    
    # 🌟 NUEVA URL para el modal AJAX
    path('equipo/guardar-tipo/', views.guardar_tipo_equipo, name='guardar_tipo_equipo'),
    
    # 🌟 NUEVA URL para búsqueda de autocompletado 🌟
    path('equipo/buscar-tipo/', views.buscar_tipo_equipo, name='buscar_tipo_equipo'),

    # URLs de MARCA
    path('equipo/guardar-marca/', views.guardar_marca, name='guardar_marca'),
    # 🌟 NUEVA URL para búsqueda de autocompletado de MARCA 🌟
    path('equipo/buscar-marca/', views.buscar_marca, name='buscar_marca'), 
    
    
    path('equipo/guardar-modelo/', views.guardar_modelo, name='guardar_modelo'),
    path('equipo/buscar-modelo/', views.buscar_modelo, name='buscar_modelo'),

    path('equipo/buscar-serie/', views.buscar_equipo_existente, name='buscar_equipo_existente'),

]