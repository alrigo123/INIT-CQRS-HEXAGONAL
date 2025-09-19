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

---

## 1. Descripción General

Este INIT aplica:

* **Hexagonal**: el **dominio** es independiente de frameworks/infraestructura.
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

---

## 3. Arquitectura

### 3.1. Hexagonal (Puertos y Adaptadores)

* **Dominio**: entidades y puertos (`repositories.py`) **sin** dependencias de infraestructura.
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
 │   │   └─ handlers/               # handlers for commands & querys.
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
 │           ├─ rabbitmq_consumer.py
 │           └─ start_consumer.py
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
         ├─ messaging/
         │   ├─ rabbitmq_publisher.py
         │   ├─ rabbitmq_consumer.py
         │   └─ start_consumer.py
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

---

## 5. Contextos Implementados

### 5.1. `users`

* **Dominio**: `User`, `UserRepository` (puerto).
* **Aplicación**:

  * **Command**: `CreateUserCommand` (+ handler).
  * **Query**: `GetUserQuery` (+ handler).
* **Infraestructura**:

  * **API**: `POST /api/v1/users/`, `GET /api/v1/users/{id}`.
  * **Persistencia**: `SQLAlchemyUserRepository`.
  * **Mensajería**: `RabbitMQPublisher` (publica `CreateUserCommand`) y `RabbitMQConsumer` (consume y persiste).
  * **Hashing**: `bcrypt` en el **consumer** (no se guarda password plano).

### 5.2. `auth`

* **Dominio**: entidades/VOs y puertos mínimos para tokens/credenciales.
* **Aplicación**:

  * **Command**: `LoginCommand` (síncrono).
  * **Query**: `ValidateTokenQuery`.
* **Infraestructura**:

  * **API**: `POST /api/v1/auth/login`, `POST /api/v1/auth/validate-token`.
  * **Persistencia**: modelos/repos de `auth`.

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

---

## 7. Cómo Ejecutar

### 7.1. Prerrequisitos

* Docker & Docker Compose
* (Opcional) Python 3.10+ para correr local sin Docker
* Extraer carpet zip INIT-CQRS-HEXAGONAL 
* o clonar repositorio 
```bash 
git clone https://github.com/alrigo123/INIT-CQRS-HEXAGONAL.git
```

### 7.2. Levantar con Docker

```bash
# Posicionarse en root 'INIT-CQRS-HEXAGONAL'
docker-compose down
docker-compose up --build
```

Contenedores esperados:

* **db** (PostgreSQL)
* **rabbitmq** (UI: [http://localhost:15672](http://localhost:15672))
* **api** (FastAPI: [http://localhost:8000](http://localhost:8000))
* **users\_consumer** (worker de comandos `users`)
* **auth\_consumer** (worker de comandos `auth`)

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
# --- EN ENVIRONMENT DE Python --- #
# DOMINIO
coverage run --source=app/users/domain,app/auth/domain -m pytest tests/users/domain/ tests/auth/domain/ 
coverage report

# APPLICACION
coverage run --source=app/users/application,app/auth/application -m pytest tests/users/application/ tests/auth/application/
coverage report

# (Opcional) HTML:
coverage html
```

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
* **Observabilidad**: logging estructurado y correlation-id entre publisher/consumer.