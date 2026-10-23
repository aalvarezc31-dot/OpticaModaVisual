"""
Carga un catálogo inicial de productos y servicios.

    python manage.py cargar_catalogo

- Usa las categorías y marcas que ya existen en la BD (por nombre).
- No duplica: si un código ya existe, lo salta.
- Registra cada producto con negocio.servicios.productos, así que el stock
  inicial queda como movimiento de ENTRADA (como exige la BD).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from negocio.excepciones import ReglaNegocioError
from negocio.servicios import catalogos, productos

# (código, nombre, categoría, marca, modelo, color, material, costo, venta, stock, mínimo)
PRODUCTOS = [
    # Lentes oftálmicos
    ("LO-001", "Lente monofocal CR-39", "LENTE OFTALMICO", "Genérico", "Monofocal", None, "CR-39", 60, 150, 40, 10),
    ("LO-002", "Lente monofocal policarbonato antirreflejo", "LENTE OFTALMICO", "Essilor", "Crizal", None, "Policarbonato", 180, 420, 25, 6),
    ("LO-003", "Lente bifocal flat-top", "LENTE OFTALMICO", "Kodak Lens", "FT-28", None, "CR-39", 150, 350, 15, 4),
    ("LO-004", "Lente progresivo digital", "LENTE OFTALMICO", "Essilor", "Varilux Comfort", None, "Orgánico 1.60", 650, 1450, 10, 3),
    ("LO-005", "Lente progresivo premium", "LENTE OFTALMICO", "ZEISS", "SmartLife", None, "Orgánico 1.67", 950, 2100, 6, 2),
    ("LO-006", "Lente con filtro de luz azul", "LENTE OFTALMICO", "Hoya", "BlueControl", None, "Orgánico 1.56", 220, 520, 20, 5),
    ("LO-007", "Lente fotocromático", "LENTE OFTALMICO", "Shamir", "Transitions Gen S", "Gris", "Orgánico 1.56", 320, 750, 12, 4),
    ("LO-008", "Lente alto índice 1.74", "LENTE OFTALMICO", "Seiko Optical", "Super Thin", None, "Orgánico 1.74", 800, 1800, 5, 2),

    # Lentes de contacto
    ("LC-001", "Lentes de contacto diarios (caja 30)", "LENTE DE CONTACTO", "Acuvue", "1-Day Moist", None, "Hidrogel", 220, 395, 30, 8),
    ("LC-002", "Lentes de contacto mensuales (caja 6)", "LENTE DE CONTACTO", "Air Optix", "Plus HydraGlyde", None, "Silicona hidrogel", 280, 490, 25, 6),
    ("LC-003", "Lentes de contacto mensuales (caja 6)", "LENTE DE CONTACTO", "Biofinity", "Biofinity", None, "Silicona hidrogel", 300, 520, 20, 5),
    ("LC-004", "Lentes de contacto tóricos (caja 6)", "LENTE DE CONTACTO", "Proclear", "Toric", None, "Hidrogel", 340, 610, 10, 3),
    ("LC-005", "Lentes de contacto quincenales (caja 6)", "LENTE DE CONTACTO", "Biomedics", "55 Evolution", None, "Hidrogel", 150, 280, 20, 5),
    ("LC-006", "Lentes de contacto mensuales (caja 6)", "LENTE DE CONTACTO", "Avaira Vitality", "Vitality", None, "Silicona hidrogel", 240, 430, 15, 4),
    ("LC-007", "Lentes de contacto diarios (caja 30)", "LENTE DE CONTACTO", "SofLens", "Daily Disposable", None, "Hidrogel", 190, 350, 15, 4),

    # Monturas
    ("MO-001", "Montura acetato clásica", "MONTURA", "Ben & Frank", "Classic", "Carey", "Acetato", 280, 650, 12, 3),
    ("MO-002", "Montura metálica ovalada", "MONTURA", "Vogue Eyewear", "VO4084", "Dorado", "Metal", 420, 950, 8, 2),
    ("MO-003", "Montura deportiva", "MONTURA", "Arnette", "AN7181", "Negro mate", "Inyectado", 380, 820, 8, 2),
    ("MO-004", "Montura infantil flexible", "MONTURA", "Miraflex", "MF-4004", "Azul", "Silicona", 300, 620, 10, 3),
    ("MO-005", "Montura infantil irrompible", "MONTURA", "Nano Vista", "Crew", "Rojo", "Siliflex", 340, 700, 8, 2),
    ("MO-006", "Montura económica", "MONTURA", "OptiPlus", "OP-120", "Negro", "Metal", 90, 250, 25, 6),
    ("MO-007", "Montura al aire (sin aro)", "MONTURA", "Genérico", "Rimless", "Plateado", "Titanio", 200, 480, 10, 3),

    # Lentes de sol
    ("LS-001", "Lentes de sol polarizados", "LENTE DE SOL", "Polaroid", "PLD 2097", "Negro", "Inyectado", 260, 590, 12, 3),
    ("LS-002", "Lentes de sol urbanos", "LENTE DE SOL", "Hawkers", "One Raw", "Carey", "TR90", 180, 420, 15, 4),
    ("LS-003", "Lentes de sol deportivos", "LENTE DE SOL", "Tifosi", "Swank", "Blanco", "Grilamid", 230, 520, 10, 3),
    ("LS-004", "Lentes de sol surf", "LENTE DE SOL", "Mormaii", "Joaca", "Azul", "Inyectado", 210, 480, 10, 3),
    ("LS-005", "Lentes de sol lectura", "LENTE DE SOL", "Foster Grant", "Sun Readers", "Negro", "Plástico", 90, 220, 12, 3),
    ("LS-006", "Lentes de sol unisex", "LENTE DE SOL", "Izipizi", "Sun #C", "Verde", "Acetato", 240, 540, 8, 2),

    # Accesorios
    ("AC-001", "Estuche rígido para lentes", "ACCESORIO", "Genérico", None, "Negro", "Rígido", 12, 35, 60, 15),
    ("AC-002", "Paño de microfibra", "ACCESORIO", "OptiPlus", None, "Gris", "Microfibra", 3, 15, 100, 25),
    ("AC-003", "Líquido limpiador de lentes 60 ml", "ACCESORIO", "OptiPlus", None, None, None, 10, 30, 50, 12),
    ("AC-004", "Solución multipropósito lentes de contacto 360 ml", "ACCESORIO", "Genérico", None, None, None, 35, 75, 30, 8),
    ("AC-005", "Cordón sujetador de lentes", "ACCESORIO", "Genérico", None, "Variado", "Nylon", 5, 20, 40, 10),
]

# (código, nombre, precio de lista, descripción). El precio se puede cambiar en cada venta.
SERVICIOS = [
    ("SV-001", "Examen visual completo", 150, "Agudeza visual, refracción y evaluación general."),
    ("SV-002", "Consulta oftalmológica", 250, "Consulta con médico oftalmólogo."),
    ("SV-003", "Control / seguimiento", 100, "Cita de control posterior a un tratamiento."),
    ("SV-004", "Adaptación de lentes de contacto", 200, "Prueba, adaptación y enseñanza de uso."),
    ("SV-005", "Medición de presión intraocular", 75, "Tonometría."),
    ("SV-006", "Topografía corneal", 350, "Estudio de la superficie de la córnea."),
    ("SV-007", "Montaje de lentes en montura", 50, "Corte y montaje de lentes."),
    ("SV-008", "Ajuste y reparación de montura", 35, "Ajuste, cambio de plaquetas o tornillos."),
    ("SV-009", "Cirugía refractiva LASIK (por ojo)", 6500, "Precio de referencia; se ajusta según evaluación."),
    ("SV-010", "Cirugía de cataratas (por ojo)", 9000, "Precio de referencia; depende del lente intraocular."),
]


class _UsuarioSistema:
    """Las cargas quedan registradas a nombre del usuario 'admin'."""

    def get_username(self):
        return "admin"


class Command(BaseCommand):
    help = "Carga productos y servicios de ejemplo usando las categorías y marcas existentes."

    def handle(self, *args, **opciones):
        categorias = {c.nombre.upper(): c.id_categoria for c in catalogos.categorias()}
        marcas = {m.nombre.upper(): m.id_marca for m in catalogos.marcas()}
        usuario = _UsuarioSistema()
        creados = saltados = 0

        filas = [
            dict(codigo=codigo, nombre=nombre, categoria=categoria, marca=marca,
                 modelo=modelo, color=color, material=material, costo=costo,
                 venta=venta, stock=stock, minimo=minimo, servicio=False, descripcion=None)
            for (codigo, nombre, categoria, marca, modelo, color, material,
                 costo, venta, stock, minimo) in PRODUCTOS
        ] + [
            dict(codigo=codigo, nombre=nombre, categoria="SERVICIO", marca=None,
                 modelo=None, color=None, material=None, costo=0, venta=venta,
                 stock=0, minimo=0, servicio=True, descripcion=descripcion)
            for (codigo, nombre, venta, descripcion) in SERVICIOS
        ]

        for fila in filas:
            if fila["categoria"] not in categorias:
                self.stderr.write(f"Sin categoría {fila['categoria']}: salto {fila['codigo']}")
                saltados += 1
                continue

            try:
                productos.registrar(usuario, {
                    "codigo": fila["codigo"],
                    "nombre": fila["nombre"],
                    "id_categoria": categorias[fila["categoria"]],
                    "id_marca": marcas.get((fila["marca"] or "").upper()),
                    "id_proveedor": None,
                    "modelo": fila["modelo"],
                    "color": fila["color"],
                    "material": fila["material"],
                    "descripcion": fila["descripcion"],
                    "es_servicio": fila["servicio"],
                    "precio_costo": Decimal(fila["costo"]),
                    "precio_venta": Decimal(fila["venta"]),
                    "stock_minimo": fila["minimo"],
                    "stock_inicial": fila["stock"],
                })
                creados += 1
            except ReglaNegocioError as error:
                self.stdout.write(f"  {fila['codigo']}: {error.mensaje} (saltado)")
                saltados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {creados} creados, {saltados} saltados."
        ))
