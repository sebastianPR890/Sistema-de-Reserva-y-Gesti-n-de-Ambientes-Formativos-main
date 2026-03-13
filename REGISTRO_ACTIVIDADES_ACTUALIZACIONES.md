# Registro de Actividades - Sistema de Auditoría Implementado

## 📋 Resumen de Cambios

Se ha implementado un sistema completo de auditoría que registra **todas las actualizaciones** de registros en el sistema, mostrando exactamente qué cambió, de qué valor a qué valor.

## 🔍 Cambios Implementados

### 1. Mejoría en `actividad/utils.py`

Se agregaron dos nuevas funciones:

```python
def registrar_actualizacion(usuario, objeto, cambios, modulo='sistema', request=None)
```
- Registra actualizaciones con detalles de qué cambió
- Captura automáticamente la IP del usuario
- Formatea los cambios de forma legible

```python
def capturar_cambios(instancia_antes, instancia_despues, campos_a_comparar)
```
- Compara dos instancias del mismo objeto
- Detecta qué campos cambieron
- Retorna diccionario con antes/después

### 2. Módulos Ahora Se Registran Actualizaciones

#### **Reservas** (`reservas/views.py`)
Registra cambios cuando se:
- ✅ Editan detalles (fecha, propósito, asistentes, observaciones)
- ✅ Aprueban reservas
- ✅ Cancelan reservas

**Ejemplo de entrada en registro:**
```
Acción: "Actualización de Reserva 45"
Cambios: 
- estado: 'Pendiente' → 'Aprobada'
- fecha_inicio: '2025-03-15 10:00' → '2025-03-20 14:00'
Módulo: reservas
```

#### **Usuarios** (`usuarios/views.py`)
Registra cambios cuando se:
- ✅ Editan datos de usuario (nombres, apellidos, email, teléfono, rol)
- ✅ Edita su propio perfil
- ✅ Se aprueba/rechaza solicitud de cambio de rol

**Ejemplo de entrada en registro:**
```
Acción: "Actualización de Usuario Juan Pérez"
Cambios:
- rol: 'usuario' → 'instructor'
- telefono: '3001234567' → '3009876543'
Módulo: usuarios
```

#### **Ambientes** (`ambientes/views.py`)
Registra cambios cuando se:
- ✅ Editan propiedades del ambiente (nombre, capacidad, tipo, ubicación)
- ✅ Se activa/desactiva un ambiente

**Ejemplo de entrada en registro:**
```
Acción: "Actualización de Ambiente Laboratorio de Sistemas"
Cambios:
- capacidad: '30' → '35'
- ubicacion: 'Piso 2' → 'Piso 3'
Módulo: ambientes
```

#### **Equipos** (`equipos/views.py`)
Registra cambios cuando se:
- ✅ Editan propiedades del equipo (código, serie, estado)
- ✅ Se activa/desactiva un equipo

**Ejemplo de entrada en registro:**
```
Acción: "Actualización de Equipo Proyector #12"
Cambios:
- estado: 'Disponible' → 'Mantenimiento'
- serie: 'SN-12345' → 'SN-12346'
Módulo: equipos
```

#### **Solicitudes de Cambio de Rol** (`usuarios/views.py`)
Registra cambios cuando se:
- ✅ Aprueban solicitudes de rol
- ✅ Rechazan solicitudes de rol

**Ejemplo de entrada en registro:**
```
Acción: "Actualización de Solicitud de rol - María García"
Cambios:
- estado: 'Pendiente' → 'Aprobada'
- rol: 'instructor' → 'coordinador'
Módulo: usuarios
```

## 🎯 Campos Monitoreados por Módulo

| Módulo | Campos Auditados |
|--------|-----------------|
| **Reservas** | fecha_inicio, fecha_fin, proposito, numero_asistentes, observaciones, ambiente, estado |
| **Usuarios** | nombres, apellidos, email, telefono, rol, activo |
| **Ambientes** | nombre, codigo, descripcion, capacidad, tipo, ubicacion, activo |
| **Equipos** | codigo, nombre, serie, estado, descripcion, activo |
| **Roles** | estado, rol |

## 📊 Cómo Mejora la Auditoría

**Antes:**
- ❌ Solo se registraban creaciones y eliminaciones
- ❌ No se sabía qué cambió en los registros editados
- ❌ Imposible rastrear cambios en estados y propiedades

**Ahora:**
- ✅ Se registran TODAS las actualizaciones
- ✅ Se muestra exactamente QUÉ cambió (campo, valor anterior, valor nuevo)
- ✅ Se registra QUIÉN realizó el cambio
- ✅ Se registra CUÁNDO se realizó
- ✅ Se registra DESDE DÓNDE (IP del usuario)

## 🔧 Uso en Código

Para agregar auditoría a nuevas funciones de edición:

```python
from actividad.utils import registrar_actualizacion, capturar_cambios
from copy import deepcopy

# En tu vista de actualización:
if request.method == 'POST':
    objeto_antes = deepcopy(objeto)  # Capturar antes
    
    # ... guardar cambios ...
    
    # Detectar qué cambió
    cambios = capturar_cambios(objeto_antes, objeto_actualizado, 
                               ['campo1', 'campo2', 'campo3'])
    
    # Registrar la actualización
    if cambios:
        registrar_actualizacion(
            usuario=request.user,
            objeto=f'TipoObjeto {objeto.nombre}',
            cambios=cambios,
            modulo='nombre_modulo',
            request=request
        )
```

## 📝 Ver Registros de Actividad

Para ver todos los cambios registrados, los administradores pueden:
1. Ir a **Actividad** → **Registro de Actividad**
2. Filtrar por módulo (Reservas, Usuarios, Ambientes, Equipos)
3. Buscar por descripción para ver qué cambió exactamente

## ✅ Estado: Completado

Sistema de auditoría para actualizaciones completamente implementado en todos los módulos principales.
