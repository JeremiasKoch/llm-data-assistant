# Usamos una imagen base de Python con Debian
FROM python:3.11-slim

# Instalamos dependencias necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos requerimientos e instalamos dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt
# Copiamos el resto de la aplicación
COPY . .

# Exponemos el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]