from datetime import timedelta

from django.utils import timezone

from datos.repositorios import reportes as repo_reportes


def resumen(dias=30):
    desde = timezone.now().date() - timedelta(days=dias - 1)
    diarias = repo_reportes.ventas_diarias(desde)
    saldos = repo_reportes.saldos_pendientes()

    return {
        "dias": dias,
        "ventas_diarias": diarias,
        "total_periodo": sum((d["total_vendido"] or 0) for d in diarias),
        "ventas_periodo": sum((d["cantidad_ventas"] or 0) for d in diarias),
        "por_vendedor": repo_reportes.ventas_por_vendedor(),
        "mas_vendidos": repo_reportes.productos_mas_vendidos(),
        "stock_bajo": repo_reportes.stock_bajo(),
        "saldos": saldos,
        "saldo_total": sum((s["saldo"] or 0) for s in saldos),
    }
