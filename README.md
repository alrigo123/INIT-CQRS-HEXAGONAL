# Backend Hexagonal CQRS — Init Project

Proyecto base en **Python** con **Arquitectura Hexagonal**, **CQRS** y **bundle-contexts** (`users`, `auth`). Sirve como esqueleto modular y escalable para backend, con separación clara entre **dominio**, **aplicación** e **infraestructura**.

Incluye **API REST con FastAPI**, **RabbitMQ** para comandos (CQRS de escritura) y **SQLAlchemy + PostgreSQL** para persistencia. Usa **DI (inyección de dependencias)** centralizada.

---

## Tabla de Contenidos

* [1. Descripción General](#1-descripción-general)
* [2. Tecnologías Utilizadas](#2-tecnologías-utilizadas)
* [3. Arquitectura](#3-arquitectura)

  * [3.1. Hexagonal (Puertos y Adaptadores)](#31-hexagonal-puertos-y-adaptadores)
  * [3.2. CQRS](#32-cqrs)
  * [3.3. Bundle-contexts](#33-bundle-contexts)
* [4. Estructura del Proyecto](#4-estructura-del-proyecto)
* [5. Contextos Implementados](#5-contextos-implementados)

  * [5.1. `users`](#51-users)
  * [5.2. `auth`](#52-auth)
* [6. Flujos Principales](#6-flujos-principales)

  * [6.1. Crear Usuario (Command → RabbitMQ)](#61-crear-usuario-command--rabbitmq)
  * [6.2. Obtener Usuario por ID (Query)](#62-obtener-usuario-por-id-query)
  * [6.3. Iniciar Sesión (Command síncrono)](#63-iniciar-sesión-command-síncrono)
  * [6.4. Validar Token (Query)](#64-validar-token-query)
* [7. Cómo Ejecutar](#7-cómo-ejecutar)

  * [7.1. Prerrequisitos](#71-prerrequisitos)
  * [7.2. Levantar con Docker](#72-levantar-con-docker)
  * [7.3. Endpoints útiles](#73-endpoints-útiles)
* [8. Pruebas y Cobertura](#8-pruebas-y-cobertura)
* [9. Decisiones Arquitectónicas](#9-decisiones-arquitectónicas)
* [10. Contribuciones](#10-contribuciones)
* [11. Licencia](#11-licencia)

---

## 1. Descripción General

Este INIT aplica:

* **Hexagonal**: el **dominio** es independiente de frameworks/infra.
* **CQRS**:

  * **Escritura (Commands)** → se publican a **RabbitMQ** y los procesa un **worker** (consumidor).
  * **Lectura (Queries)** → acceden directamente al modelo de lectura (repositorio SQL).
* **Bundle-contexts**: `users` y `auth` con sus tres capas (`domain`, `application`, `infrastructure`).
* **DI**: contenedor compartido para bajo acoplamiento.

---

## 2. Tecnologías Utilizadas

* **Python** 3.10+
* **FastAPI** (API REST)
* **SQLAlchemy** (ORM)
* **PostgreSQL** (BD)
* **RabbitMQ** (mensajería para Commands)
* **pika** (cliente RabbitMQ)
* **bcrypt** (hashing de contraseñas)
* **pydantic** (DTO/validación)
* **pytest**, **coverage** (pruebas)
* **Docker** & **Docker Compose**

> 🔄 Se **elimina** del README anterior: `passlib` y el “RegisterUserCommand” de `auth` (no se usa en el proyecto actual).

---

## 3. Arquitectura

### 3.1. Hexagonal (Puertos y Adaptadores)

* **Dominio**: entidades y puertos (`repositories.py`) **sin** dependencias de infra.
* **Aplicación**: casos de uso en **handlers** que reciben puertos/servicios por **DI**.
* **Infraestructura**: adaptadores concretos (API, repos SQLAlchemy, RabbitMQ).

### 3.2. CQRS

* **Commands** (escritura) → publicados a **RabbitMQ** y ejecutados por **consumidores** (workers).
* **Queries** (lectura) → llamadas directas a repos de lectura.

> En este proyecto, **`users` usa RabbitMQ** para Commands; **`auth` opera de forma síncrona** (login/validate).

### 3.3. Bundle-contexts

* Cada contexto (`users`, `auth`) tiene `domain/`, `application/`, `infrastructure`.
* Facilita escalar, testear y reemplazar implementaciones.

---

## 4. Estructura del Proyecto

```bash
app/
 ├─ main.py                         # Entrypoint FastAPI (routers, startup)
 ├─ shared/
 │   └─ di_container.py             # Fábricas/DI para repos, servicios, etc.
 ├─ users/
 │   ├─ domain/
 │   │   ├─ models.py               # Entidad de dominio User
 │   │   └─ repositories.py         # Puerto: UserRepository
 │   ├─ application/
 │   │   ├─ commands/
 │   │   │   └─ create_user_command.py
 │   │   ├─ queries/
 │   │   │   └─ get_user_query.py
 │   │   └─ handlers/               # handle_create_user, handle_get_user...
 │   └─ infrastructure/
 │       ├─ api/v1/
 │       │   ├─ routes.py           # POST /users, GET /users/{id}
 │       │   └─ schemas.py
 │       ├─ persistence/
 │       │   ├─ database.py         # Engine/Session/Base/create_tables
 │       │   ├─ user_model.py       # Modelo ORM
 │       │   └─ repositories.py     # SQLAlchemyUserRepository (adaptador)
 │       └─ messaging/
 │           ├─ rabbitmq_publisher.py
 │           └─ rabbitmq_consumer.py
 └─ auth/
     ├─ domain/
     │   ├─ models.py               # (p.ej., Token / credenciales)
     │   └─ repositories.py
     ├─ application/
     │   ├─ commands/               # LoginCommand (síncrono)
     │   ├─ queries/                # ValidateTokenQuery
     │   └─ handlers/
     └─ infrastructure/
         ├─ api/v1/
         │   ├─ routes.py           # POST /auth/login, POST /auth/validate-token
         │   └─ schemas.py
         └─ persistence/
             ├─ database.py         # comparte/coordina Base
             ├─ auth_model.py
             └─ repositories.py

tests/
 └─ ... (por context y capa)

Dockerfile
docker-compose.yml                 # (API, db, rabbitmq, workers)
requirements.txt
```

> ❗️**Nota**: En tu ZIP hay archivos con `...` (elipses) en `main.py` y `docker-compose.yml`.
> Aquí documentamos **la intención final**; ajusta tu repo para que coincida.

---

## 5. Contextos Implementados

### 5.1. `users`

* **Dominio**: `User`, `UserRepository` (puerto).
* **Aplicación**:

  * **Command**: `CreateUserCommand` (+ handler).
  * **Query**: `GetUserQuery` (+ handler).
* **Infra**:

  * **API**: `POST /api/v1/users/`, `GET /api/v1/users/{id}`.
  * **Persistencia**: `SQLAlchemyUserRepository`.
  * **Mensajería**: `RabbitMQPublisher` (publica `CreateUserCommand`) y `RabbitMQConsumer` (consume y persiste).
  * **Hashing**: `bcrypt` en el **consumer** (no se guarda password plano).

### 5.2. `auth`

* **Dominio**: entidades/VOs y puertos mínimos para tokens/credenciales.
* **Aplicación**:

  * **Command**: `LoginCommand` (síncrono).
  * **Query**: `ValidateTokenQuery`.
* **Infra**:

  * **API**: `POST /api/v1/auth/login`, `POST /api/v1/auth/validate-token`.
  * **Persistencia**: modelos/repos de `auth`.
  * **Mensajería**: **no usada** actualmente en `auth` (se elimina “RegisterUserCommand” del README anterior).

---

## 6. Flujos Principales

### 6.1. Crear Usuario (Command → RabbitMQ)

1. `POST /api/v1/users/` recibe `name`, `email`, `password`.
2. El endpoint construye `CreateUserCommand` y lo **publica** a RabbitMQ.
3. El **consumer** deserializa, **hashea** con `bcrypt` y **persiste** vía `UserRepository`.
4. La API responde confirmando aceptación (procesamiento asíncrono).

### 6.2. Obtener Usuario por ID (Query)

1. `GET /api/v1/users/{id}`.
2. El endpoint llama el **handler** de `GetUserQuery` → repositorio de lectura.
3. Retorna `200 OK` con los datos.

### 6.3. Iniciar Sesión (Command síncrono)

1. `POST /api/v1/auth/login` con `email`, `password`.
2. Handler valida credenciales (consulta usuarios) y **emite token** si es válido.
3. Respuesta `200 OK` con `{ access_token, token_type }`.

### 6.4. Validar Token (Query)

1. `POST /api/v1/auth/validate-token` con `access_token`.
2. Handler verifica existencia/expiración.
3. Respuesta con `{ is_valid, user_id?, exp? }`.

> 🕒 Recomendación: usar tiempos **UTC aware** (`datetime.now(timezone.utc)`) para evitar errores tipo *“can't compare offset-naive and offset-aware datetimes”*.

---

## 7. Cómo Ejecutar

### 7.1. Prerrequisitos

* Docker & Docker Compose
* (Opcional) Python 3.10+ para correr local sin Docker

### 7.2. Levantar con Docker

```bash
docker-compose down
docker-compose up --build
```

Contenedores esperados:

* **db** (PostgreSQL)
* **rabbitmq** (UI: [http://localhost:15672](http://localhost:15672))
* **api** (FastAPI: [http://localhost:8000](http://localhost:8000))
* **users\_consumer** (worker de comandos `users`)

> Ajusta nombres/variables según tu `docker-compose.yml` definitivo.

### 7.3. Endpoints útiles

* **Docs**: `http://localhost:8000/docs`
* **Users**:

  * `POST /api/v1/users/`
  * `GET /api/v1/users/{id}`
* **Auth**:

  * `POST /api/v1/auth/login`
  * `POST /api/v1/auth/validate-token`

---

## 8. Pruebas y Cobertura

Ejecutar pruebas:

```bash
pytest -v
```

Cobertura:

```bash
coverage run -m pytest
coverage report -m
# (Opcional) HTML:
coverage html
```

> Objetivo: **≥ 80% en la capa de dominio** (según la consigna del PDF).
> No incluimos un porcentaje “fijo” aquí para evitar desalinearse del repo real.

---

## 9. Decisiones Arquitectónicas

* **Hexagonal**: dominio **puro** y estable; infra reemplazable (SQL, mensajería, web).
* **CQRS**:

  * **Commands** asíncronos → **users** con RabbitMQ.
  * **Queries** síncronas → acceso directo a repos de lectura.
* **Bundle-contexts**: `users` y `auth` desacoplados; facilita evolución independiente.
* **DI**: `shared/di_container.py` centraliza construcción/inyectables.
* **Persistencia**: SQLAlchemy; recomendable unificar `Base`/metadata y orquestar `create_all()` en `startup`.
* **Seguridad**: hashing con **bcrypt** en el worker; tokens validados con tiempos UTC.
* **Observabilidad** (recomendado): logging estructurado y correlation-id entre publisher/consumer.

---

## 10. Contribuciones

Proyecto de prueba técnica: no se esperan contribuciones externas.

## 11. Licencia

MIT (ver `LICENSE`).

---

### Cambios vs. README anterior (resumen)

* ❌ Removido: `RegisterUserCommand` en `auth` y su flujo asociado.
* ❌ Removido: referencia a `passlib`.
* ✅ Aclarado: **`auth` opera síncrono** (login/validate).
* ✅ Conservado: Commands de **`users`** por **RabbitMQ**; Queries directas.
* ✅ Añadido: advertencia sobre **datetimes aware** para tokens.
* ✅ Alineado a tu árbol real (DI, consumidores, hashing con `bcrypt`).
