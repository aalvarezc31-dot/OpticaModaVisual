# Óptica Moda Visual — Arquitectura por capas

El proyecto está organizado en **3 capas**. Cada capa solo puede usar
a la capa que tiene debajo:

```
┌──────────────────────────────┐
│  PRESENTACIÓN  (presentacion)│  vistas, formularios, URLs, plantillas HTML
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  NEGOCIO       (negocio)     │  servicios: reglas y casos de uso
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  DATOS         (datos)       │  modelos ORM + repositorios (consultas)
└──────────────┬───────────────┘
               ▼
        SQL Server (OpticaModaVisual)
        esquemas: citas, clientes, clinica, facturacion,
                  inventario, seguridad, ventas, reportes
```

## Módulos del sistema

| Menú | Qué hace |
|---|---|
| Inicio | Indicadores: clientes, citas de hoy, ventas de hoy, alertas de stock |
| Clientes | Lista con filtros, alta, edición, activar/desactivar y **ficha** con historial (citas, exámenes, recetas, ventas) |
| Citas | Agenda con filtros por estado/fecha; confirmar, atender, no asistió, cancelar (con motivo); optometrista asignado |
| Clínica → Exámenes | Registro (se puede abrir desde una cita), detalle del examen |
| Clínica → Resultados | Resultados de exámenes, registro de receta, **receta imprimible** |
| Ventas | Venta con productos, descuento, confirmación, pagos parciales, entrega y anulación |
| Facturas | Emisión desde una venta, factura imprimible con IVA, anulación |
| Inventario | Productos (alta, edición, ficha, movimientos de stock), proveedores, categorías y marcas |
| Reportes | Ventas diarias, por vendedor, más vendidos, saldos por cobrar, stock bajo |

## Reglas importantes (vienen de la base de datos)

- **El stock solo cambia con movimientos** (`inventario.movimiento_inventario`).
  El trigger `trg_movimiento_ai` suma/resta y no deja que quede negativo.
  Por eso el stock inicial de un producto se registra como una ENTRADA y el
  formulario de edición no permite cambiar el stock.
- **Flujo de una venta** (trigger `trg_venta_au`):
  `PENDIENTE → CONFIRMADA → PAGADA → ENTREGADA`, y se puede `ANULAR` antes de entregar.
  - Solo en PENDIENTE se agregan/quitan productos (trigger `trg_detalle_venta_aiud`,
    que además recalcula el subtotal).
  - Al CONFIRMAR se descuenta el inventario (SALIDA por producto).
  - Los pagos se registran sobre una venta CONFIRMADA; al cubrir el total pasa a PAGADA.
  - Al ANULAR una venta confirmada o pagada se devuelve el inventario (ENTRADA).
  - Si la venta tiene factura vigente, primero hay que anular la factura.
- **Facturas**: una por venta (`uq_factura_venta`), el número sale de la
  secuencia `facturacion.seq_numero_factura` y el IVA lo calcula la columna `monto_iva`.
  El descuento general de la venta se reparte entre las líneas para que la
  factura sume exactamente el total.
- **Columnas calculadas** (`venta.total`, `detalle_venta.subtotal`, `factura.monto_iva`,
  `factura_detalle.total`) están declaradas como `GeneratedField`: Django nunca las escribe.
- Los mensajes de error de los triggers (p. ej. *"Stock insuficiente..."*) se
  muestran al usuario tal cual (`negocio/excepciones.py → desde_error_bd`).

## Productos y servicios

- Un **servicio** (consulta, examen, cirugía, ajuste...) es un producto con
  "Es un servicio" marcado: no maneja stock y en la venta **se le puede cambiar
  el precio** según el caso. Los productos siempre se venden a su precio de lista
  (para rebajar se usa el descuento).
- La receta en una venta es opcional: se pueden vender lentes de sol, monturas,
  accesorios o servicios sin receta.
- Catálogo inicial: `python manage.py cargar_catalogo`
  (`presentacion/management/commands/cargar_catalogo.py`). Usa las categorías y
  marcas existentes y no duplica códigos; edita las listas del archivo para
  cargar otros productos.

- **Cobrar una cita**: botón *Cobrar* en Citas. Crea la venta del paciente con el
  servicio del tipo de cita (`SERVICIO_POR_TIPO_CITA` en `negocio/servicios/ventas.py`)
  y no la duplica si se pulsa otra vez.

## Flujo clínico

Cita → (atendida) → Examen visual → Receta óptica (opcional) → Venta.
La receta solo se registra a partir de un examen; la venta puede llevarla o no.

## Panel administrativo (/admin/)

Accesible desde el menú **Admin** para usuarios con permiso de staff
(código en `presentacion/admin.py`). Muestra:
- **Roles** y **Usuarios del sistema (con rol)**: tablas `seguridad.rol` y
  `seguridad.usuario`. El rol y el estado se cambian en la misma lista
  (botón *Guardar*). El botón *Agregar cuentas de login que faltan* trae las
  cuentas de Django que aún no tienen usuario del sistema.
- **Usuarios** de Django (cuentas de login) con la columna *Rol en el sistema*.
  Al crear o guardar una cuenta se crea/actualiza su usuario del sistema
  (ADMINISTRADOR si es superusuario, si no VENDEDOR).

## Usuario que registra las operaciones

El login usa las cuentas de Django (`auth_user`). Las operaciones se guardan a
nombre del usuario de `seguridad.usuario` **con el mismo username**. Si no existe,
se usa `ID_USUARIO_SISTEMA_PREDETERMINADO` (en `config/settings.py`, hoy = 1).
Para que cada persona quede registrada con su nombre, crea en `seguridad.usuario`
un registro con el mismo username de su cuenta de Django.

## Fechas y hora

`USE_TZ = False` y `TIME_ZONE = 'America/Guatemala'`: Django guarda la hora
local, igual que `sysdatetime()` y las vistas del esquema `reportes`.

## Estructura de carpetas

```
OpticaModaVisual/
├── config/                     settings, urls raíz, formatos de número/fecha (config/formatos)
│
├── presentacion/               CAPA DE PRESENTACIÓN
│   ├── urls.py                 Todas las rutas
│   ├── views/                  autenticacion, inicio, clientes, citas, examenes, recetas,
│   │                           ventas, facturas, productos, catalogos, reportes
│   ├── forms/                  Validación de lo que escribe el usuario
│   ├── utilidades.py           paginación y manejo de errores en formularios
│   ├── middleware.py           RecursoNoEncontrado → página 404
│   ├── context_processors.py   marca la sección activa del menú
│   └── templates/presentacion/ Plantillas (base.html tiene los estilos compartidos)
│
├── negocio/                    CAPA DE NEGOCIO
│   ├── excepciones.py          ReglaNegocioError, RecursoNoEncontrado, desde_error_bd
│   └── servicios/              sesion, panel, clientes, citas, examenes, recetas,
│                               productos, catalogos, ventas, facturas, reportes
│
└── datos/                      CAPA DE DATOS
    ├── models/                 Un archivo por esquema de la BD
    └── repositorios/           Único lugar con consultas: clientes, citas, clinica,
                                productos, inventario, ventas, facturas, usuarios, reportes
```

## Reglas para seguir programando

1. **Las vistas no consultan la BD.** Una vista lee el `request`, valida el
   formulario, llama a un servicio de `negocio` y muestra la plantilla.
2. **Las reglas van en `negocio/servicios`.** Si algo no se permite, el servicio
   lanza `ReglaNegocioError("mensaje", campo="opcional")` y la vista lo muestra
   con `mostrar_error(request, form, error)`.
3. **Solo `datos/repositorios` usa `Modelo.objects`.** Si necesitas una consulta
   nueva, agrégala como función en el repositorio correspondiente.
4. Los formularios `ModelForm` pueden referenciar un modelo para definir sus
   campos, pero **guardan a través del servicio**, nunca con `form.save()`.
5. Para actualizar registros usa `Modelo.objects.filter(pk=...).update(...)`
   (como hacen los repositorios): `instancia.save()` reescribe todas las columnas
   y pisaría valores que mantienen los triggers.

### Ejemplo: agregar un módulo nuevo

1. `datos/repositorios/<modulo>.py` → `listar()`, `crear(**datos)`
2. `negocio/servicios/<modulo>.py` → `buscar()`, `registrar(datos)` con las reglas
3. `presentacion/forms/<modulo>.py` → el formulario
4. `presentacion/views/<modulo>.py` + rutas en `presentacion/urls.py`
5. `presentacion/templates/presentacion/<modulo>.html` (usa las clases de `base.html`:
   `pagina-cabecera`, `panel`, `busqueda`, `tabla-wrap`, `btn`, `estado`...)
6. Agrega la opción al menú en `base.html` y la sección en `context_processors.py`

## Cómo ejecutar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

La base de datos **no cambia**: todos los modelos siguen con `managed = False`
y los mismos `db_table`, así que no hay que correr migraciones nuevas.
