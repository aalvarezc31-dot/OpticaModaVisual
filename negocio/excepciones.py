import re


class ReglaNegocioError(Exception):
    """
    Se lanza cuando una operacion viola una regla del negocio.

    `campo` indica (opcionalmente) a que campo del formulario
    pertenece el error, para que la capa de presentacion lo muestre ahi.
    """

    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo


class RecursoNoEncontrado(Exception):
    """El registro solicitado no existe."""


def desde_error_bd(error, por_defecto):
    """
    Convierte un error de SQL Server en ReglaNegocioError.

    Los triggers de la BD lanzan mensajes propios con THROW 50000+
    (p. ej. "Stock insuficiente..."); esos se muestran tal cual.
    Cualquier otro error muestra el mensaje `por_defecto`.
    """
    texto = str(error)
    coincidencia = re.search(r"\[SQL Server\]([^\[]+?)\s*\(5\d{4}\)", texto)

    if coincidencia:
        return ReglaNegocioError(coincidencia.group(1).strip())

    return ReglaNegocioError(por_defecto)
