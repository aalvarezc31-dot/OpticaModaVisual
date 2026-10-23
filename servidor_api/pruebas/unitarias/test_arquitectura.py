"""
Arquitectura N-tier: verifica en el código fuente que ninguna capa se salte a otra.

    Nivel 1  servidor_web/presentacion  -> solo habla HTTP con la API (sin BD)
    Nivel 2  servidor_api/api           -> negocio
             servidor_api/negocio       -> datos
             servidor_api/datos         -> (nada del sistema)
    Nivel 3  SQL Server

Falla si alguien agrega un import que rompa estas reglas.
"""
import ast
from pathlib import Path

from django.test import SimpleTestCase

RAIZ = Path(__file__).resolve().parents[3]
API = RAIZ / "servidor_api"
WEB = RAIZ / "servidor_web"


def modulos_importados(carpeta):
    """{archivo: {paquete raíz importado}} para todo .py de la carpeta (sin pruebas)."""
    resultado = {}
    for archivo in carpeta.rglob("*.py"):
        if "pruebas" in archivo.parts or "migrations" in archivo.parts:
            continue
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        nombres = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                nombres.update(alias.name.split(".")[0] for alias in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                nombres.add(nodo.module.split(".")[0])
        resultado[archivo.relative_to(RAIZ)] = nombres
    return resultado


class ArquitecturaEnCapas(SimpleTestCase):
    def assertNoImporta(self, carpeta, prohibidos):
        for archivo, nombres in modulos_importados(carpeta).items():
            with self.subTest(archivo=str(archivo)):
                self.assertFalse(nombres & prohibidos, f"{archivo} importa {nombres & prohibidos}")

    def test_presentacion_no_toca_negocio_ni_datos_ni_bd(self):
        self.assertNoImporta(WEB, {"negocio", "datos", "api", "backoffice", "pyodbc", "mssql"})

    def test_datos_no_depende_de_capas_superiores(self):
        self.assertNoImporta(API / "datos", {"negocio", "api", "backoffice", "presentacion"})

    def test_negocio_no_depende_de_http_ni_de_presentacion(self):
        self.assertNoImporta(API / "negocio", {"api", "backoffice", "presentacion"})

    def test_servidor_web_sin_base_de_datos(self):
        configuracion = (WEB / "config" / "settings.py").read_text(encoding="utf-8")
        self.assertIn("DATABASES = {}", configuracion)
        requisitos = (WEB / "requirements.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("mssql", requisitos)
        self.assertNotIn("pyodbc", requisitos)
