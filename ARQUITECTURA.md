# Óptica Moda Visual — Arquitectura en capas física (N-tier)

El sistema está dividido en **tres niveles que corren por separado**. Cada nivel
solo se comunica con el que tiene inmediatamente debajo:

```
 Navegador
    │  HTTP (páginas HTML)
    ▼
┌──────────────────────────────────────────────┐
│ NIVEL 1 · servidor_web       (puerto 8000)   │  Presentación: vistas, formularios,
│   presentacion/                              │  plantillas, dashboard, exportación.
│   SIN base de datos y sin driver de SQL      │  Pide todo a la API.
└──────────────────────┬───────────────────────┘
                       │  HTTP + JSON  (token firmado en cada petición)
                       ▼
┌──────────────────────────────────────────────┐
│ NIVEL 2 · servidor_api       (puerto 8010)   │  Aplicación:
│   api/        adaptador HTTP (endpoints)     │   - api      → recibe la petición, valida token y permiso
│   negocio/    reglas y casos de uso          │   - negocio  → reglas del negocio
│   datos/      modelos ORM + repositorios     │   - datos    → única capa que consulta la BD
│   backoffice/ panel admin + comandos         │
└──────────────────────┬───────────────────────┘
                       │  ODBC
                       ▼
┌──────────────────────────────────────────────┐
│ NIVEL 3 · SQL Server  (OpticaModaVisual)     │  Esquemas por módulo, triggers,
│                                              │  columnas calculadas, vistas de reportes
└──────────────────────────────────────────────┘
```

Por qué NO es un monolito:

- Son **dos programas independientes**, cada uno con su `manage.py`, su
  `config/settings.py` y su `requirements.txt`. Se pueden instalar en máquinas distintas.
- El servidor web **no tiene base de datos** (`DATABASES = {}`) ni el driver de
  SQL Server en sus requisitos: todo pasa por la API (`presentacion/cliente_api.py`).
- La API vuelve a validar el **token** y el **permiso por rol** en cada operación,
  aunque la llamen sin pasar por el servidor web.
- `servidor_api/pruebas/unitarias/test_arquitectura.py` revisa el código y falla
  si alguna capa importa otra que no le corresponde.

## La API (nivel 2)

| Método y ruta | Qué hace |
|---|---|
| `GET /api/v1/` | Estado del servidor y catálogo de operaciones publicadas |
| `POST /api/v1/sesion/` | Login: usuario + contraseña → token, rol y secciones permitidas |
| `POST /api/v1/<módulo>/<operación>/` | Ejecuta una operación del negocio. Cuerpo `{"args": [...], "kwargs": {...}}` |

Respuestas: `200` resultado · `401` sin token o vencido · `403` el rol no tiene
permiso · `404` operación o registro inexistente · `422` regla de negocio
(`{"mensaje", "campo"}`) · `400` argumentos inválidos.

Solo se pueden llamar las operaciones listadas en `api/operaciones.py`, cada una
con la sección que exige (Inicio, Clientes, Citas, Clínica, Ventas, Facturas,
Inventario, Reportes). Fechas y decimales viajan marcados (`{"$fecha": ...}`,
`{"$decimal": ...}`) para no perder precisión.

## Estructura de carpetas

```
OpticaModaVisual/
├── servidor_web/                 NIVEL 1 — Presentación
│   ├── manage.py · requirements.txt (Django, openpyxl; sin driver de BD)
│   ├── config/                   settings (URL de la API, sesión en cookie firmada)
│   ├── presentacion/
│   │   ├── cliente_api.py        ÚNICO punto de contacto con la API (HTTP)
│   │   ├── servicios.py          módulos remotos: clientes, citas, ventas…
│   │   ├── sesion.py · middleware.py   login, permisos del menú, errores de la API
│   │   ├── views/ · forms/ · templates/
│   │   └── exportar.py           Excel (.xlsx) y CSV
│   └── pruebas/                  unitarias + integración entre niveles
│
└── servidor_api/                 NIVEL 2 — Aplicación
    ├── manage.py · requirements.txt (Django, mssql-django, pyodbc)
    ├── config/                   settings (BD, token, pruebas)
    ├── api/                      endpoints, token, serialización, catálogo de operaciones
    ├── negocio/
    │   ├── excepciones.py
    │   └── servicios/            clientes, citas, examenes, recetas, ventas, facturas,
    │                             productos, catalogos, panel, reportes, permisos, usuarios
    ├── datos/
    │   ├── models/               un archivo por esquema de la BD
    │   └── repositorios/         consultas (incluye reportes e integridad)
    ├── backoffice/               panel /admin/ y comandos de mantenimiento
    └── pruebas/                  unitarias + integración con la BD
```

## Cómo ejecutar

Se necesitan **dos terminales** (o dos ventanas de PowerShell).

**Terminal 1 — servidor de aplicación (API):**
```bash
cd servidor_api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 8010
```

**Terminal 2 — servidor web:**
```bash
cd servidor_web
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 8000
```

Abrir http://127.0.0.1:8000. El panel administrativo está en http://127.0.0.1:8010/admin/
(o desde el botón **Admin** del menú).

Variables de entorno opcionales (para desplegar en otras máquinas):

| Variable | Servidor | Por defecto |
|---|---|---|
| `OPTICA_API_URL` | web | `http://127.0.0.1:8010` |
| `OPTICA_DB_HOST`, `OPTICA_DB_NAME` | api | `ANDY\MSSQLSERVER123`, `OpticaModaVisual` |
| `OPTICA_API_SECRET_KEY`, `OPTICA_WEB_SECRET_KEY` | api / web | clave de desarrollo |
| `OPTICA_API_HOSTS`, `OPTICA_WEB_HOSTS` | api / web | `localhost,127.0.0.1` |
| `OPTICA_DEBUG` | ambos | `1` |

> En esta computadora el puerto 8001 lo usa Cisco Packet Tracer; por eso la API usa el 8010.

## Pruebas

| Batería | Comando | Necesita |
|---|---|---|
| Unitarias de la API (69) | `cd servidor_api` → `python manage.py test pruebas.unitarias` | Nada |
| Integración con la BD (12) | `python manage.py preparar_bd_pruebas` → `python manage.py test pruebas.integracion` | Copia de la BD |
| Unitarias del web (18) | `cd servidor_web` → `python manage.py test pruebas.unitarias` | Nada |
| Integración entre niveles (8) | ver abajo | API encendida sobre la copia |
| Integridad de datos (15 reglas) | `cd servidor_api` → `python manage.py verificar_integridad` | Solo lectura |

Integración entre niveles:
```bash
cd servidor_api
python manage.py preparar_bd_pruebas
set OPTICA_DB_NAME=OpticaModaVisual_pruebas
python manage.py crear_usuarios_prueba
python manage.py runserver 8010
```
y en otra terminal:
```bash
cd servidor_web
python manage.py test pruebas
```

Las pruebas con base de datos **nunca tocan la base real**: corren sobre la copia
`OpticaModaVisual_pruebas` (`preparar_bd_pruebas`, respaldo `COPY_ONLY`). Para
borrarla: `python manage.py preparar_bd_pruebas --eliminar`.

## Reglas importantes de la base de datos

- **El stock solo cambia con movimientos** (trigger `trg_movimiento_ai`): el stock
  inicial es una ENTRADA y los ajustes del admin son movimientos de AJUSTE.
- **Flujo de una venta** (trigger `trg_venta_au`): `PENDIENTE → CONFIRMADA → PAGADA → ENTREGADA`;
  se puede `ANULAR` antes de entregar. Confirmar descuenta stock; anular lo devuelve.
- **Facturas**: una por venta, número de la secuencia `facturacion.seq_numero_factura`,
  IVA calculado por la columna `monto_iva`.
- Un `THROW` dentro de un trigger **revierte la transacción completa** en SQL Server.
  Por eso cada operación corre en su propia transacción (y las pruebas que provocan
  esos errores no se envuelven en otra).

## Permisos por rol

| Rol | Ve |
|---|---|
| ADMINISTRADOR, VENDEDOR, superusuarios | Todo |
| OPTOMETRISTA | Inicio (sin montos), Clientes, Citas y Clínica |

Definidos en `servidor_api/negocio/servicios/permisos.py`. El servidor web oculta
el menú; la API rechaza con `403` cualquier operación no permitida.

## Cómo agregar un módulo

1. `servidor_api/datos/repositorios/<modulo>.py` — consultas.
2. `servidor_api/negocio/servicios/<modulo>.py` — reglas.
3. `servidor_api/api/operaciones.py` — publicar las operaciones y su sección.
4. `servidor_web/presentacion/servicios.py` — `nuevo = Modulo("<modulo>")`.
5. `servidor_web/presentacion/forms`, `views`, `urls.py` y la plantilla.
