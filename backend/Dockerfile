# Usamos una imagen oficial de Python como base
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos
COPY requirements.txt .

# Instalamos todas las librerías necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de nuestra aplicación
COPY . .

# El comando que se ejecutará cuando el contenedor inicie
CMD ["flask", "run", "--host=0.0.0.0"]
