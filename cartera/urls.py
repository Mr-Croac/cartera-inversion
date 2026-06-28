from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('buscar/', views.buscar_tickers, name='buscar'),
    path('historial/', views.historial_precios, name='historial'),
    path('compras/', views.registrar_compra, name='registrar_compra'),
    path('precio/', views.precio_actual, name='precio_actual'),
    path('vender/', views.vender, name='vender'),
    path('descargar/', views.descargar_registro, name='descargar'),
    path('alerta/crear/', views.crear_alerta, name='crear_alerta'),
    path('alerta/borrar/<int:alerta_id>/', views.borrar_alerta, name='borrar_alerta'),
    path('alertas-ticker/', views.alertas_ticker, name='alertas_ticker'),
    path('ingresar/', views.ingresar_fondos, name='ingresar_fondos'),
    path('noticias/', views.noticias_ticker, name='noticias_ticker'),
    path('rsi/', views.indicador_rsi, name='indicador_rsi'),
    path('macd/', views.indicador_macd, name='indicador_macd'),
    path('bollinger/', views.indicador_bollinger, name='indicador_bollinger'),
]