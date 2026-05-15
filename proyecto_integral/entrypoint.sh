#!/bin/sh

echo "Ejecutando migraciones..."
python manage.py migrate

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Creando superusuario por defecto (si no existe)..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@medici.com', 'admin123')" | python manage.py shell

echo "Iniciando servidor..."

exec "$@"