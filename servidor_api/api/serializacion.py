"""
Conversión entre objetos de Python y JSON para viajar entre servidores.

JSON no tiene fechas ni decimales, así que se envían marcados:
    {"$fecha": "2026-10-22"}, {"$fechahora": "2026-10-22T10:30:00"}, {"$decimal": "750.00"}
El servidor web usa las mismas marcas para reconstruirlos.
"""
from datetime import date, datetime, time
from decimal import Decimal

from django.db.models import Model, QuerySet


def a_json(valor):
    """Convierte lo que devuelve un servicio en algo que json.dumps acepta."""
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    if isinstance(valor, Decimal):
        return {"$decimal": str(valor)}
    if isinstance(valor, datetime):
        return {"$fechahora": valor.replace(tzinfo=None).isoformat()}
    if isinstance(valor, date):
        return {"$fecha": valor.isoformat()}
    if isinstance(valor, time):
        return {"$hora": valor.isoformat()}
    if isinstance(valor, Model):
        return _registro(valor)
    if isinstance(valor, dict):
        return {str(clave): a_json(v) for clave, v in valor.items()}
    if isinstance(valor, (list, tuple, set, frozenset, QuerySet)):
        return [a_json(v) for v in valor]
    raise TypeError(f"No se puede enviar un {type(valor).__name__} por la API.")


# Nombres del contrato de la API cuando difieren de la columna de SQL Server.
# (La base conserva vendedor_*; el sistema llama "Agente" a ese rol.)
ALIAS_CAMPOS = {
    "id_vendedor": "id_agente",
    "vendedor_nombre": "agente_nombre",
}


def _registro(instancia):
    """Un registro del ORM como diccionario con todas sus columnas (incluidas las calculadas)."""
    datos = {ALIAS_CAMPOS.get(campo.attname, campo.attname): a_json(getattr(instancia, campo.attname))
             for campo in instancia._meta.concrete_fields}
    datos["pk"] = a_json(instancia.pk)
    return datos


def desde_json(valor):
    """Reconstruye fechas y decimales en los argumentos que llegan del servidor web."""
    if isinstance(valor, list):
        return [desde_json(v) for v in valor]
    if isinstance(valor, dict):
        if len(valor) == 1:
            (marca, texto), = valor.items()
            if marca == "$decimal":
                return Decimal(texto)
            if marca == "$fecha":
                return date.fromisoformat(texto)
            if marca == "$fechahora":
                return datetime.fromisoformat(texto)
            if marca == "$hora":
                return time.fromisoformat(texto)
        return {clave: desde_json(v) for clave, v in valor.items()}
    return valor
