"""
Módulos remotos del servidor de aplicación.

Las vistas los usan igual que antes usaban la capa de negocio, pero cada
llamada es una petición HTTP a la API (ver cliente_api.py).
"""
from presentacion.cliente_api import Modulo

panel = Modulo("panel")
clientes = Modulo("clientes")
citas = Modulo("citas")
examenes = Modulo("examenes")
recetas = Modulo("recetas")
productos = Modulo("productos")
catalogos = Modulo("catalogos")
ventas = Modulo("ventas")
facturas = Modulo("facturas")
reportes = Modulo("reportes")
