# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instala dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código fuente de la aplicación al contenedor.)
COPY . .

# Comando por defecto para ejecutar la aplicación
CMD ["echo", "Aplicación backend. Usa docker-compose para ejecutar con servicios."]