# ⚡ Guía de Instalación Rápida

Para usuarios con experiencia previa. Lee [README.md](README.md) para instrucciones detalladas.

## Requisitos
- Python 3.13.5
- MySQL 8.0
- Git (opcional)

## Pasos

### 1. Clonar y Configurar

```bash
git clone <REPO_URL>
cd Sistema-de-Reserva-y-Gesti-n-de-Ambientes-Formativos-main

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Base de Datos

```bash
# Conectar a MySQL y ejecutar script
mysql -u root -p < sistema_reservas.sql

# O en MySQL CLI:
source sistema_reservas.sql
```

### 3. Variables de Entorno

Crear `sistema_reservas/.env`:

```env
SECRET_KEY=<generar-con-python-get_random_secret_key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=sistema_reservas
DB_USER=sistema_reservas_user
DB_PASSWORD=masterpassword
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST_USER=tu@gmail.com
EMAIL_HOST_PASSWORD=app_password_16_digitos
```

### 4. Migraciones y Usuario Admin

```bash
cd sistema_reservas

python manage.py migrate
python manage.py createsuperuser
```

### 5. Ejecutar

```bash
python manage.py runserver
```

Accede a: http://localhost:8000/admin/

---

## 🚨 Problemas Frecuentes

| Error | Solución |
|-------|----------|
| `python: comando no encontrado` | Agrega Python al PATH o usa `python3` |
| `No module named 'django'` | Activa venv: `.\venv\Scripts\activate` |
| `Can't connect to MySQL` | Verifica que MySQL está corriendo y credenciales en `.env` |
| `ModuleNotFoundError: mysqlclient` | `pip install mysqlclient` |
| `SECRET_KEY not found` | Crea `.env` en carpeta `sistema_reservas/` |
| Puerto 8000 en uso | `python manage.py runserver 8001` |

---

Ver [README.md](README.md) para detalles completos y troubleshooting avanzado.
