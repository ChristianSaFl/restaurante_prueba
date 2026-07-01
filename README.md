# Restaurante Final — Sistema de Gestión de Restaurante

Proyecto Final — Ingeniería de Software II (2026)
Universidad Católica San Pablo (UCSP)

---

## Índice

1. [Integrante](#1-integrante)
2. [Propósito del proyecto](#2-propósito-del-proyecto)
3. [Funcionalidades](#3-funcionalidades)
4. [Arquitectura](#4-arquitectura)
5. [Módulos y servicios REST](#5-módulos-y-servicios-rest)
6. [Pipeline CI/CD](#6-pipeline-cicd)
7. [Gestión de tareas e issues](#7-gestión-de-tareas-e-issues)
8. [Planificación de release](#8-planificación-de-release)
9. [Cómo ejecutar el proyecto](#9-cómo-ejecutar-el-proyecto)

---

## 1. Integrante

Proyecto desarrollado de forma individual.

| Nombre | Usuario GitHub |
|---|---|
| Christian | [@ChristianSaFl](https://github.com/ChristianSaFl) |

---

## 2. Propósito del proyecto

**Restaurante Final** es una aplicación web para la gestión integral de un restaurante: control de mesas, productos del menú, pedidos, facturación y reservas. El proyecto evoluciona un sistema previo desarrollado en cursos anteriores, incorporando:

- Un **pipeline de integración y despliegue continuo (CI/CD)** completo sobre Jenkins.
- La separación del módulo de reservas en un **microservicio REST independiente**.
- Automatización de pruebas unitarias, funcionales, de rendimiento y de seguridad.
- Despliegue automático mediante contenedores Docker.

---

## 3. Funcionalidades

La aplicación cubre el ciclo completo de operación de un restaurante:

- **Autenticación**: login/logout con roles de usuario (admin, staff).
- **Gestión de mesas**: alta de mesas, ocupar/liberar, consulta de disponibilidad.
- **Gestión de productos (menú)**: alta, edición y eliminación de productos con validación de nombre y precio.
- **Gestión de pedidos**: creación de pedidos, agregar/quitar ítems, cierre de pedido.
- **Facturación**: generación de boleta a partir de un pedido, aplicación de descuentos y propinas, marcado de pago, cálculo automático de impuestos (IGV 18%).
- **Reservas**: creación, confirmación, cancelación y eliminación de reservas — implementado como microservicio REST independiente del monolito principal.
- **Reportes**: vista consolidada de la operación del restaurante.
- **Administración de usuarios**: alta y baja de usuarios del sistema (solo admin).

> Las funcionalidades pueden verificarse directamente navegando la aplicación desplegada (ver [sección 9](#9-cómo-ejecutar-el-proyecto)); no se incluye diagrama de casos de uso UML en esta entrega.

---

## 4. Arquitectura

El proyecto sigue un enfoque inspirado en **Domain-Driven Design (DDD)**, separando el código en capas con responsabilidades claras:

```
src/main/python/
├── domain/                     # Capa de dominio (lógica de negocio pura, sin dependencias de framework)
│   ├── entities/                → Bill, Order, Product, Table
│   ├── repositories/             → contratos de persistencia (BillRepository, OrderRepository, TableRepository)
│   └── services/                 → BillingService, OrderService, TableService
│
├── infrastructure/             # Detalles técnicos (acceso a base de datos)
│   └── database.py
│
├── web/                         # Capa de presentación (monolito Flask, MVC)
│   └── app.py                    → rutas, controladores, plantillas Jinja2
│
└── microservices/
    └── reservations_service/    # Microservicio independiente (API REST) para el módulo de Reservas
        └── app.py
```

**Patrón de arquitectura:** MVC + Módulos por capas (dominio / infraestructura / web), con el módulo de Reservas evolucionado hacia una arquitectura de **microservicios** — expone su propia API REST y su propio modelo de datos (`Reservation`), desacoplado del monolito principal.

**Entidades de dominio principales:**

| Entidad | Responsabilidad |
|---|---|
| `Product` | Representa un producto del menú (nombre, precio). Valida que el nombre no esté vacío y el precio sea positivo. |
| `Table` | Representa una mesa (número, capacidad, estado ocupado/libre). Expone `occupy()` / `release()` con validación de estado. |
| `Order` | Representa un pedido: colección de productos con cantidad. Calcula el total. |
| `Bill` | Representa la boleta generada a partir de un `Order`. Aplica descuento (máx. 50%), propina e impuesto (18%), calcula el total final. |

**Stack tecnológico:**

- **Backend:** Python 3.12, Flask 3.x
- **ORM:** Flask-SQLAlchemy
- **Base de datos:** PostgreSQL (alojada en [Neon](https://neon.tech))
- **Frontend:** HTML + Jinja2 + CSS (server-rendered)
- **Servidor WSGI (producción):** Gunicorn
- **Contenerización:** Docker (multi-stage build)

> No se incluye diagrama de clases ni diagrama de paquetes en esta entrega; la estructura de módulos se documenta en el árbol de directorios anterior.

---

## 5. Módulos y servicios REST

### 5.1 Aplicación web principal (`web/app.py`)

Aplicación monolítica renderizada en servidor (no es una API REST pura). Rutas principales:

| Módulo | Método | Ruta | Descripción |
|---|---|---|---|
| Auth | GET/POST | `/login` | Inicio de sesión |
| Auth | GET | `/logout` | Cierre de sesión |
| Productos | GET | `/products` | Listado de productos |
| Productos | GET/POST | `/products/new` | Crear producto |
| Productos | GET/POST | `/products/<id>/edit` | Editar producto |
| Productos | POST | `/products/<id>/delete` | Eliminar producto |
| Mesas | GET | `/tables` | Listado de mesas |
| Mesas | GET/POST | `/tables/new` | Crear mesa |
| Mesas | POST | `/tables/<number>/occupy` | Ocupar mesa |
| Mesas | POST | `/tables/<number>/release` | Liberar mesa |
| Pedidos | GET | `/orders` | Listado de pedidos |
| Pedidos | GET/POST | `/orders/new` | Crear pedido |
| Pedidos | GET | `/orders/<id>` | Detalle de pedido |
| Pedidos | POST | `/orders/<id>/close` | Cerrar pedido |
| Pedidos | POST | `/orders/<id>/add-item` | Agregar ítem al pedido |
| Pedidos | POST | `/orders/<id>/remove-item/<iid>` | Quitar ítem del pedido |
| Boletas | GET | `/bills` | Listado de boletas |
| Boletas | POST | `/bills/generate/<order_id>` | Generar boleta desde un pedido |
| Boletas | GET | `/bills/<id>` | Detalle de boleta |
| Boletas | POST | `/bills/<id>/discount` | Aplicar descuento |
| Boletas | POST | `/bills/<id>/tip` | Aplicar propina |
| Boletas | POST | `/bills/<id>/pay` | Marcar boleta como pagada |
| Reservas | GET/POST | `/reservations`, `/reservations/new` | Vista web de reservas (consume el microservicio) |
| Reportes | GET | `/reports` | Reporte consolidado |
| Administración | GET/POST | `/admin/users`, `/admin/users/new` | Gestión de usuarios |

### 5.2 Microservicio de Reservas (`microservices/reservations_service/app.py`)

API REST en formato JSON, independiente del monolito, con su propio modelo de datos (`Reservation`).

**Modelo `Reservation`:**

```json
{
  "id": "integer",
  "customer_name": "string (requerido)",
  "customer_phone": "string (opcional)",
  "table_id": "integer (opcional)",
  "guests": "integer (requerido)",
  "date": "string, formato YYYY-MM-DD (requerido)",
  "time": "string, formato HH:MM (requerido)",
  "status": "string: pending | confirmed | cancelled",
  "notes": "string (opcional, máx. 300 caracteres)"
}
```

**Endpoints:**

| Método | URL | Descripción | Respuesta |
|---|---|---|---|
| `GET` | `/api/health` | Health check del servicio | `200 { status, service }` |
| `GET` | `/api/reservations` | Lista todas las reservas ordenadas por fecha/hora | `200 [Reservation]` |
| `POST` | `/api/reservations` | Crea una nueva reserva | `201 Reservation` \| `400 { error }` |
| `PUT` | `/api/reservations/<id>/confirm` | Confirma una reserva pendiente | `200 Reservation` \| `404 { error }` |
| `PUT` | `/api/reservations/<id>/cancel` | Cancela una reserva | `200 Reservation` \| `404 { error }` |
| `DELETE` | `/api/reservations/<id>` | Elimina una reserva | `200` \| `404 { error }` |

> Documentación en formato Swagger/OpenAPI pendiente de generar; la tabla anterior resume el contrato de la API.

---

## 6. Pipeline CI/CD

Implementado en **Jenkins** mediante un `Jenkinsfile` declarativo. Se dispara automáticamente ante cada `push` al repositorio (`githubPush()` trigger). Etapas:

| # | Etapa | Herramienta | Detalle |
|---|---|---|---|
| 1 | **Construcción Automática** | `venv` + `pip` | Crea entorno virtual, instala dependencias (`requirements.txt`) y empaqueta la app en una imagen Docker (etapa 7) |
| 2 | **Análisis Estático** | SonarQube | Analiza `src/`, valida Quality Gate (timeout 2 min) antes de continuar |
| 3 | **Pruebas Unitarias** | pytest + coverage | Ejecuta pruebas de dominio, servicios y repositorios; genera reporte de cobertura HTML/XML |
| 4 | **Pruebas Funcionales** | Selenium (Chrome headless) | Pruebas end-to-end sobre la app corriendo con Gunicorn; valida flujos de creación de productos vía navegador |
| 5 | **Pruebas de Performance** | Apache JMeter | Ejecuta plan de pruebas contra la app; genera reporte HTML de resultados |
| 6 | **Pruebas de Seguridad** | OWASP ZAP | Spider + Active Scan contra la app corriendo; genera reporte HTML de alertas |
| 7 | **Build de imagen Docker** | Docker | Build multi-stage de la imagen de producción |
| 8 | **Despliegue Automático** | Docker | Detiene el contenedor anterior y despliega la nueva imagen (`docker run`), usando variables de entorno inyectadas vía credenciales de Jenkins |

Todas las etapas están integradas en un único pipeline y se ejecutan de forma secuencial en cada build; los reportes de cada herramienta (cobertura, Selenium, JMeter, ZAP) se publican como artefactos HTML en Jenkins.

---

## 7. Gestión de tareas e issues

El seguimiento del proyecto se realiza mediante **GitHub Project** (tablero Kanban) con las siguientes columnas:

`TO DO` → `CURRENT ITERATION` → `In Progress` → `FIX VALIDATION` → `Done`

Cada tarjeta del tablero está vinculada a un **GitHub Issue** del repositorio, lo que permite trazabilidad entre la planificación y los commits que resuelven cada issue (mediante referencias `Fix #N` en los mensajes de commit).

---

## 8. Planificación de release

Flujo seguido: **GitHub Project → Issues → Commits → GitHub Release**.

Las tareas se planifican en el Project, se materializan como Issues, se resuelven mediante commits referenciados (`Fix #N`) en las ramas de trabajo, y se integran vía Pull Request hacia `development` y `master` siguiendo el flujo:

```
feature/* → development → master
```

---

## 9. Cómo ejecutar el proyecto

### Con Docker Compose (recomendado)

```bash
docker compose up -d
```

Esto levanta: la aplicación web (`app`), el microservicio de reservas (`reservations`), SonarQube y Jenkins.

### Manualmente

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://<usuario>:<password>@<host-neon>/<db>"
export SECRET_KEY="tu-secret-key"
export ADMIN_INITIAL_PASSWORD="admin123"
export STAFF_INITIAL_PASSWORD="staff123"

gunicorn -w 1 -b 0.0.0.0:8083 src.main.python.web.app:app
```

La aplicación queda disponible en `http://localhost:8083`.
