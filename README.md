# TPI-OE
trabajo practico integrados organizacion empresarial

# Gestor de Vacaciones

Sistema de gestión de solicitudes de vacaciones por consola, desarrollado en Python con almacenamiento en CSV.

## Estructura del proyecto

```
matematica/
├── main.py               # Interfaz de usuario y flujos de navegación
├── utils.py              # Lógica de negocio, validaciones y acceso a datos
└── data/
    ├── usuarios.csv      # Base de usuarios del sistema
    └── solicitudes.csv   # Registro de solicitudes de vacaciones
```

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas (solo librería estándar)

## Cómo ejecutar

```bash
python3 main.py
```

## Roles del sistema

| Rol       | Descripción                                              |
|-----------|----------------------------------------------------------|
| empleado  | Solicita vacaciones y consulta el estado de sus pedidos  |
| jefatura  | Preaprueba o rechaza solicitudes enviadas por empleados  |
| rrhh      | Aprueba o rechaza solicitudes preaprobadas por jefatura  |

## Flujo de una solicitud

```
Empleado solicita
      ↓
PENDIENTE_PREAPROBACION
      ↓  Jefatura preaprueba / rechaza
PENDIENTE_APROBACION  ←→  RECHAZADA
      ↓  RRHH aprueba / rechaza
  APROBADA            ←→  RECHAZADA
```

## Reglas de negocio

- La fecha de inicio de las vacaciones debe ser un **lunes**.
- Las vacaciones se toman en **bloques de 7 días**.
- No se puede solicitar más días de los disponibles.
- El login tiene un límite de **3 intentos** antes de bloquear el acceso.

## Usuarios de prueba

| Usuario      | Contraseña | Rol      | Días disponibles |
|--------------|------------|----------|-----------------|
| `jperez`     | `1234`     | empleado | 7               |
| `mgarcia`    | `1234`     | empleado | 21              |
| `lsanchez`   | `1234`     | empleado | 7               |
| `clopez`     | `1234`     | jefatura | —               |
| `arodriguez` | `1234`     | rrhh     | —               |

## Estructura de los CSVs

**`data/usuarios.csv`**

| Campo             | Descripción                          |
|-------------------|--------------------------------------|
| id                | Identificador único                  |
| nombre            | Nombre completo                      |
| usuario           | Nombre de usuario para el login      |
| contrasena        | Contraseña                           |
| rol               | `empleado`, `jefatura` o `rrhh`      |
| dias_disponibles  | Días de vacaciones disponibles       |

**`data/solicitudes.csv`**

| Campo             | Descripción                                              |
|-------------------|----------------------------------------------------------|
| id                | Identificador único                                      |
| empleado_id       | ID del empleado solicitante                              |
| empleado_nombre   | Nombre del empleado                                      |
| fecha_inicio      | Fecha de inicio (`YYYY-MM-DD`)                           |
| fecha_fin         | Fecha de fin (`YYYY-MM-DD`)                              |
| dias              | Cantidad de días solicitados                             |
| estado            | `PENDIENTE_PREAPROBACION`, `PENDIENTE_APROBACION`, `APROBADA` o `RECHAZADA` |
| fecha_solicitud   | Fecha en que se realizó la solicitud (`YYYY-MM-DD`)      |
| comentario        | Motivo de rechazo (si aplica)                            |

## Arquitectura

- **`utils.py`** concentra toda la lógica de negocio y el acceso a los CSVs. No contiene ningún `print` ni `input`.
- **`main.py`** concentra toda la interacción con el usuario. No conoce el formato de los CSVs ni las reglas de negocio.
