ROOT API PROJECT (\fastAPI_server)
🔹 1. Crear un entorno virtual
> python -m venv venv

🔹 2 Activar (DEVELOPMENT)
> venv\Scripts\activate

🔹 3. Instalar FastAPI y Uvicorn
> pip install fastapi uvicorn
> pip install -r requirements.txt 

🔹 4. Crear el archivo principal
mdkir app
app/main.py:

''' 
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "¡Hola, FastAPI está funcionando!"}
@app.get("/saludo/{nombre}")
def saludo(nombre: str):
    return {"saludo": f"Hola {nombre}, bienvenido a FastAPI 🚀"}
    '''

🔹 5. Ejecutar el servidor (DEVELOPMENT)
> uvicorn app.main:app --reload


# ----------------------------------------------- #

** PARA MIGRACION DE DATA USANDO ALEMBIC (root API)  on enviroment (venv) **
1. Inicializa Alembic (una sola vez):
> pip install alembic
> python -m alembic init alembic (default)
> alembic init app/infrastructure/migrations (with path)

2. Configura la URL en alembic.ini:
> sqlalchemy.url = mariadb+mariadbconnector://user:pass@localhost:3306/emtage-inventory

3. Cuando quieras agregar una columna/tabla
* Editas app/infrastructure/orm.py (añades estado_venta, vendida_en al modelo Prenda)

3. En alembic/env.py
> '''
from logging.config import fileConfig
import os, sys
from alembic import context
from sqlalchemy import engine_from_config, pool

# Asegura que 'app' sea importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Tu app
from app.database import Base
from app.core.config import get_settings
# IMPORTA TODOS los modelos para que autogenerate los “vea”
from app.models import brand, category, color, size, product, variant, stock_movement  # noqa

config = context.config
settings = get_settings()

# Inyecta la URL desde .env
db_url = getattr(settings, "DATABASE_URL", None)
if not db_url:
    raise RuntimeError("DATABASE_URL no está definida en .env")
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", db_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

3. Crear la línea base (baseline) cundo la BD existe
Genera la revision
> alembic revision --autogenerate -m "baseline"


Esto creará un archivo en alembic/versions/*.py con los CREATE TABLE ....

Marca la BD como si ya estuviera en esa revisión (no ejecuta SQL):

alembic stamp head

Crear la BD →
Configurar la conexión en el proyecto →
Definir el modelo (entidad) →
Generar y aplicar migraciones (Alembic) →
Crear rutas/CRUD →  (CUALES SE PUEDEN BORAR,A VETEGROIAS ESASS CCOSAS)
Levantar y probar.






