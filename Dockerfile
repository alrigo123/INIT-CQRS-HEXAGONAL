# Usa una imagen base oficial de Python
# Selecciona una versión específica de Python 3.x, por ejemplo, 3.11
# Usa 'slim' para una imagen más ligera
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos primero para aprovechar la caché de Docker
# Esto evita reinstalar dependencias si requirements.txt no cambia
COPY requirements.txt .

# Instala las dependencias del proyecto
# Se recomienda usar --no-cache-dir para imágenes más ligeras
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente de la aplicación al contenedor
# Asegúrate de tener un .dockerignore para excluir archivos innecesarios (como .git, __pycache__, etc.)
COPY . .

# Comando por defecto para ejecutar la aplicación
# Este comando puede ser sobrescrito al ejecutar el contenedor
# Por ahora, solo dejamos un comando básico. Lo configuraremos mejor en docker-compose.yml
CMD ["echo", "Aplicación backend. Usa docker-compose para ejecutar con servicios."]