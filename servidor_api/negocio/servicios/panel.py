from datetime import timedelta

from django.utils import timezone

from datos.repositorios import citas as repo_citas
from datos.repositorios import clientes as repo_clientes
from datos.repositorios import productos as repo_productos
from datos.repositorios import ventas as repo_ventas

NOMBRES_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _actividad_semana(hoy):
    """Cantidad de citas durante los últimos 7 días."""
    actividad = []

    for diferencia in range(6, -1, -1):
        dia = hoy - timedelta(days=diferencia)
        actividad.append({
            "etiqueta": NOMBRES_DIAS[dia.weekday()],
            "fecha": dia.strftime("%d/%m"),
            "cantidad": repo_citas.contar_del_dia(dia),
        })

    maximo = max((dia["cantidad"] for dia in actividad), default=0)

    for dia in actividad:
        dia["porcentaje"] = (
            max(8, int(dia["cantidad"] / maximo * 100))
            if maximo else 8
        )

    return actividad


def resumen_inicio():
    hoy = timezone.now().date()
    ahora = timezone.now()

    return {
        "clientes_total": repo_clientes.contar(),
        "citas_hoy": repo_citas.contar_vigentes_del_dia(hoy),
        "citas_proximas": repo_citas.proximas_vigentes(ahora),
        "productos_total": repo_productos.contar_activos(),
        "ventas_hoy": repo_ventas.total_vendido_del_dia(hoy),
        "ventas_pendientes": repo_ventas.contar_por_estado(repo_ventas.PENDIENTE),
        "stock_bajo": repo_productos.contar_stock_bajo(),
        "actividad_semana": _actividad_semana(hoy),
        "fecha_actual": hoy,
    }
