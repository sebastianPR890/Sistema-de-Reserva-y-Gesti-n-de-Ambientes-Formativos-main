# 🏫 Sistema de Reserva y Gestión de Ambientes Formativos

> Sistema integral de gestión de espacios educativos, equipos e inventario para instituciones de formación.

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecución](#ejecución)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Guía de Uso](#guía-de-uso)
- [Troubleshooting](#troubleshooting)

---

## 📝 Descripción

Sistema web desarrollado con **Django 4.2.7** y **Python 3.13.5** que permite a instituciones educativas:

- ✅ Gestionar ambientes (aulas, laboratorios, talleres, auditorios, etc.)
- ✅ Crear y aprobar/rechazar reservas de espacios
- ✅ Administrar equipos e inventario
- ✅ Registrar auditoría de todas las operaciones
- ✅ Generar reportes en PDF
- ✅ Recibir notificaciones por email
- ✅ Realizar copias de seguridad automáticas de la base de datos
- ✅ Controlar acceso con roles y permisos
- ✅ Visualizar disponibilidad en calendario interactivo

---

## 🎯 Características Principales

| Funcionalidad | Descripción |
|---------------|------------|
| **Gestión de Ambientes** | CRUD de espacios con capacidad, recursos disponibles |
| **Sistema de Reservas** | Crear, editar, aprobar/rechazar reservas de ambientes |
| **Inventario de Equipos** | Registrar equipos, movimientos, historial |
| **Control de Usuarios** | Gestión de roles (admin, coordinador, docente, estudiante) |
| **Auditoría Completa** | Registro de todas las acciones del sistema |
| **Notificaciones** | Alertas por email de cambios en reservas |
| **Reportes PDF** | Generación de reportes de reservas y movimientos |
| **Backups Automáticos** | Copias de seguridad programadas de MySQL |
| **Accesibilidad Web** | Cumple estándares WCAG |
| **Calendario Visual** | Vista interactiva de disponibilidad |

---

## ⚙️ Requisitos Previos

Antes de instalar, asegúrate de tener:

### 1. **Python 3.13.5**
   - [Descargar desde python.org](https://www.python.org/downloads/)
   - **Importante:** Durante la instalación, marca la opción "Add Python to PATH"
   - Verifica la instalación:
     ```bash
     python --version
     # Debe mostrar: Python 3.13.5
     ```

### 2. **MySQL Server 8.0**
   - [Descargar desde dev.mysql.com](https://dev.mysql.com/downloads/mysql/)
   - Durante la instalación:
     - Nota el puerto (default: 3306)
     - Crea una contraseña para el usuario `root`
   - Verifica la instalación:
     ```bash
     mysql --version
     # O abre la consola MySQL
     ```

### 3. **Git** (Opcional, pero recomendado)
   - [Descargar desde git-scm.com](https://git-scm.com/)
   - Para clonar el repositorio

### 4. **Editor de Código** (Recomendado)
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [PyCharm Community](https://www.jetbrains.com/pycharm/download/)

---

## 🚀 Instalación

### Paso 1: Clonar el Repositorio

**Opción A - Con Git:**
```bash
git clone <URL-DEL-REPOSITORIO>
cd Sistema-de-Reserva-y-Gesti-n-de-Ambientes-Formativos-main
```

**Opción B - Descargar como ZIP:**
1. Descargar el repositorio como ZIP
2. Extraer en la ubicación deseada
3. Abrir terminal en la carpeta `sistema_reservas`

### Paso 2: Crear Entorno Virtual

```bash
# En Windows (PowerShell o CMD)
python -m venv venv

# Activar el entorno virtual
.\venv\Scripts\activate

# En Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**Nota:** Deberías ver `(venv)` al inicio de tu terminal si está activado correctamente.

### Paso 3: Actualizar pip

```bash
python -m pip install --upgrade pip
```

### Paso 4: Instalar Dependencias

```bash
# Instalar todas las dependencias del proyecto
pip install -r requirements.txt
```

**Dependencias principales:**
- Django 4.2.7
- django-crispy-forms (formularios avanzados)
- Pillow (procesamiento de imágenes)
- python-dotenv (variables de entorno)
- mysqlclient (driver de MySQL)
- reportlab (generación de PDF)
- django-ratelimit (protección contra abuso)

---

## 🔧 Configuración

### Paso 1: Crear la Base de Datos

#### Opción A - Usando MySQL CLI

1. Abre MySQL desde terminal:
   ```bash
   mysql -u root -p
   # Ingresa tu contraseña de root
   ```

2. Ejecuta el script SQL:
   ```sql
   source sistema_reservas.sql
   # O copia y pega el contenido manualmente
   ```

3. Verifica la creación:
   ```sql
   SHOW DATABASES;
   SHOW USERS;
   ```

#### Opción B - Usando MySQL Workbench

1. Conecta con tus credenciales de root
2. File → Open SQL Script → Selecciona `sistema_reservas.sql`
3. Ejecuta el script (Ctrl+Shift+Enter)

### Paso 2: Crear Archivo .env

En la carpeta `sistema_reservas/` crea un archivo llamado `.env` con:

```env
# Configuración de Django
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuración de Base de Datos
DB_NAME=sistema_reservas
DB_USER=sistema_reservas_user
DB_PASSWORD=masterpassword
DB_HOST=localhost
DB_PORT=3306

# Configuración de Email (Gmail)
# este sera el email desde el que el proyecto enviara correos a los usuarios
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_de_gmail
```

**⚠️ IMPORTANTE - Generar SECRET_KEY:**

Ejecuta en Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

**📧 Para Email con Gmail:**

1. Activa 2FA en tu cuenta Google
2. Ve a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Genera una contraseña de aplicación (16 dígitos)
4. Copia esa contraseña en `EMAIL_HOST_PASSWORD`

### Paso 3: Ejecutar Migraciones

Las migraciones crean todas las tablas en la base de datos:

```bash
# Activar entorno virtual si no está activo
.\venv\Scripts\activate  # Windows

# Aplicar migraciones
python manage.py migrate
```

Deberías ver un mensaje como:
```
Applying contenttypes.0001_initial... OK
Applying auth.0001_initial... OK
Applying usuarios.0001_initial... OK
...
```

### Paso 4: Recopilar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

---

## ▶️ Ejecución

### Crear Usuario Administrador

```bash
python manage.py createsuperuser
```

Te pedirá:
```
Documento: (tu documento)
Email: tu@email.com
Password: (contraseña)
Password (again): (confirmar)
```

### Iniciar el Servidor de Desarrollo

```bash
python manage.py runserver
```

Deberías ver:
```
Watching for file changes with StatReloader
Starting development server at http://127.0.0.1:8000/
```

### Acceder a la Aplicación

- **Panel Principal:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
  - Usuario: `admin`
  - Contraseña: (la que creaste)

---

## 📂 Estructura del Proyecto

```
sistema_reservas/
├── manage.py                    # Punto de entrada Django
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno (crear)
├── sistema_reservas.sql         # Script de BD
│
├── sistema_reservas/            # Configuración principal
│   ├── settings.py             # Configuración de Django
│   ├── urls.py                 # URLs principales
│   ├── wsgi.py                 # Configuración WSGI (producción)
│   └── asgi.py                 # Configuración ASGI (async)
│
├── actividad/                   # App de Auditoría
│   ├── models.py               # Modelo de registros
│   ├── views.py                # Vistas
│   └── migrations/             # Migraciones DB
│
├── ambientes/                   # App de Gestión de Espacios
│   ├── models.py               # Modelo Ambiente
│   ├── views.py                # Vistas CRUD
│   ├── forms.py                # Formularios
│   └── migrations/
│
├── equipos/                     # App de Inventario
│   ├── models.py               # Modelos Equipo, Movimiento
│   ├── views.py                # Vistas CRUD
│   ├── forms.py                # Formularios
│   └── migrations/
│
├── reservas/                    # App Principal - Reservas
│   ├── models.py               # Modelo Reserva, Historial
│   ├── views.py                # Vistas CRUD + Aprobación
│   ├── forms.py                # Formularios
│   ├── utils.py                # Utilidades (PDF, emails)
│   └── migrations/
│
├── usuarios/                    # App de Control de Acceso
│   ├── models.py               # Modelo Usuario personalizado
│   ├── views.py                # Vistas de perfil, solicitudes
│   ├── forms.py                # Formularios
│   └── migrations/
│
├── login/                       # App de Autenticación
│   ├── views.py                # Login, registro, logout
│   ├── forms.py                # Formularios auth
│   └── urls.py
│
├── notificaciones/              # App de Alertas
│   ├── models.py               # Modelo Notificación
│   ├── views.py                # Vistas
│   └── migrations/
│
├── calendario/                  # App de Calendario
│   ├── views.py                # API JSON de eventos
│   └── models.py
│
├── backups/                     # App de Copias de Seguridad
│   ├── views.py                # Gestión de backups
│   ├── utils.py                # Funciones MySQL dump
│   └── backups_created/        # Carpeta de archivos .sql
│
├── templates/                   # Plantillas HTML
│   ├── base.html               # Plantilla base
│   ├── index.html              # Página principal
│   ├── reservas/               # Templates de reservas
│   ├── ambientes/              # Templates de ambientes
│   ├── equipos/                # Templates de equipos
│   ├── usuarios/               # Templates de usuarios
│   ├── login/                  # Templates de auth
│   ├── email/                  # Plantillas de email
│   └── partials/               # Componentes reutilizables
│
├── static/                      # Archivos estáticos
│   ├── css/
│   │   └── estilos.css         # Estilos personalizados
│   ├── js/                     # JavaScript
│   └── logo_proyecto/          # Logos e imágenes
│
├── logs/                        # Carpeta de logs
│
└── venv/                        # Entorno virtual (no incluido)
```

---

## 🎓 Guía de Uso

### Para Administradores

1. **Acceder al Panel Admin:**
   - URL: http://localhost:8000/admin/
   - Usuario: admin, Contraseña: (creada en instalación)

2. **Crear Ambientes:**
   - Admin → Ambientes → Agregar ambiente
   - Completar: nombre, capacidad, recursos, ubicación

3. **Gestionar Usuarios:**
   - Admin → Usuarios → Crear usuario
   - Asignar roles: Administrador, Coordinador, Docente, Estudiante

4. **Aprobar/Rechazar Reservas:**
   - Panel → Reservas → Pendientes
   - Revisar detalles y aprobar o rechazar

5. **Generar Reportes:**
   - Reservas → Descargar PDF
   - Equipos → Historial de movimientos

### Para Docentes/Estudiantes

1. **Crear una Reserva:**
   - Acceder a http://localhost:8000/
   - Reservas → Nueva Reserva
   - Seleccionar: Ambiente, Fecha, Hora, Propósito

2. **Ver Estado de Reservas:**
   - Mi Panel → Mis Reservas
   - Ver estado (Pendiente, Aprobada, Rechazada)

3. **Verificar Disponibilidad:**
   - Ambientes → Calendario
   - Ver qué espacios están disponibles

---

## 🐛 Troubleshooting

### Error: "python: comando no encontrado"

**Solución:**
- Asegurate de que Python está en el PATH
- Desinstala y reinstala Python, marcando "Add Python to PATH"
- Usa `python3` en lugar de `python`

### Error: "No module named 'django'"

**Solución:**
```bash
# Verifica que el entorno virtual está activado
.\venv\Scripts\activate  # Windows

# Reinstala las dependencias
pip install -r requirements.txt
```

### Error: "django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")"

**Solución:**
1. Verifica que MySQL está corriendo:
   ```bash
   # Windows - En Services, busca MySQL
   # O desde terminal:
   mysql -u root -p
   ```

2. Verifica las credenciales en `.env`

3. Confirma que la base de datos fue creada:
   ```bash
   mysql -u root -p
   > SHOW DATABASES;
   > USE sistema_reservas;
   > SHOW TABLES;
   ```

### Error: "ModuleNotFoundError: No module named 'mysqlclient'"

**Solución (Windows):**
```bash
pip install mysqlclient
# Si falla, intenta:
pip install mysql-connector-python
```

### Las migraciones no se aplican

**Solución:**
```bash
# Ver estado de migraciones
python manage.py showmigrations

# Deshacer migraciones (cuidado!)
python manage.py migrate app_name zero

# Rehacer migraciones
python manage.py migrate
```

### Error: "SECRET_KEY not found in .env"

**Solución:**
- Crea el archivo `.env` en la carpeta `sistema_reservas/`
- Asegúrate de que la ruta es correcta
- Reinicia el servidor: Ctrl+C y vuelve a ejecutar `python manage.py runserver`

### El sitio no envía emails

**Solución:**
1. Verifica las credenciales de Gmail en `.env`
2. Genera una [contraseña de aplicación Google](https://myaccount.google.com/apppasswords)
3. Usa esa contraseña en `EMAIL_HOST_PASSWORD` (no la contraseña de cuenta)
4. Asegurate que 2FA está habilitado en tu cuenta Google
5. Prueba con:
   ```python
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@gmail.com', ['to@gmail.com'])
   ```

### Puerto 8000 ya está en uso

**Solución:**
```bash
# Usa otro puerto
python manage.py runserver 8001

# O encuentra y detén el proceso
# Windows - En Command Prompt:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Las imágenes de equipos no se cargan

**Solución:**
```bash
# Recopila los archivos estáticos
python manage.py collectstatic --noinput

# En desarrollo, asegúrate que MEDIA_URL está configurado en urls.py
```

---

## 📚 Recursos Adicionales

- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de MySQL](https://dev.mysql.com/doc/)
- [Bootstrap 4 (CSS usado)](https://getbootstrap.com/docs/4.0/)
- [python-dotenv](https://python-dotenv.readthedocs.io/)

---

## 🔒 Seguridad

**En Producción:**

1. Cambia `DEBUG=False` en `.env`
2. Genera una `SECRET_KEY` nueva y fuerte
3. Usa HTTPS
4. Configura `ALLOWED_HOSTS` con el dominio real
5. Usa una contraseña fuerte para la base de datos
6. Configura copias de seguridad automáticas
7. Implementa CSRF tokens en formularios
8. Usa variables de entorno para datos sensibles

---

## 👥 Contribución

Para reportar bugs o sugerir mejoras:
1. Abre un issue en GitHub
2. Proporciona detalles del problema
3. Incluye pasos para reproducir

---

## 📄 Licencia

Este proyecto está bajo licencia [AGREGAR LICENCIA]

---

## 📞 Soporte

Para soporte adicional:
- Contacta al equipo de desarrollo
- Revisa la sección de troubleshooting
- Consulta la documentación de Django

---

**Última actualización:** Abril 2026  
**Versión:** 1.0.0
