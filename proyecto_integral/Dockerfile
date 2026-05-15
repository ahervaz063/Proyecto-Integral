FROM python:3.12

# Instalar netcat para que entrypoint.sh pueda esperar a la base de datos
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Copiar y dar permisos al entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Puerto expuesto
EXPOSE 8000

# Entrypoint (se ejecuta antes que CMD)
ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto (desarrollo local)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]