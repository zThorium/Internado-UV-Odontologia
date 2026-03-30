FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Entrypoint: ejecuta migraciones y luego inicia el servidor
CMD ["./entrypoint.sh"]
