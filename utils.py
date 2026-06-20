import csv
from datetime import datetime, date
from pathlib import Path

# Configuración de las rutas de archivos de datos dentro del proyecto
DATA_DIR = Path(__file__).parent / 'data'
USUARIOS_CSV = DATA_DIR / 'usuarios.csv'
SOLICITUDES_CSV = DATA_DIR / 'solicitudes.csv'

# Constantes del sistema
MAX_INTENTOS = 3
DIAS_BLOQUE = 7

# Estructura de columnas para los archivos CSV
USUARIO_FIELDS = ['id', 'nombre', 'usuario', 'contrasena', 'rol', 'dias_disponibles']
SOLICITUD_FIELDS = [
    'id', 'empleado_id', 'empleado_nombre',
    'fecha_inicio', 'fecha_fin', 'dias',
    'estado', 'fecha_solicitud', 'comentario',
]

# Diccionario para traducir los estados internos a texto legible
ESTADOS = {
    'PENDIENTE_PREAPROBACION': 'Pendiente preaprobación',
    'PENDIENTE_APROBACION':    'Pendiente aprobación',
    'APROBADA':                'Aprobada',
    'RECHAZADA':               'RECHAZADA',
}


# ── I/O ───────────────────────────────────────────────────────────────────────

def cargar_usuarios():
    # Lee y retorna la lista completa de usuarios desde el archivo CSV
    with open(USUARIOS_CSV, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def guardar_usuarios(usuarios):
    # Sobrescribe el archivo CSV de usuarios con la lista de datos actualizada
    with open(USUARIOS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=USUARIO_FIELDS)
        w.writeheader()
        w.writerows(usuarios)


def cargar_solicitudes():
    # Lee y retorna la lista completa de solicitudes desde el archivo CSV
    with open(SOLICITUDES_CSV, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def guardar_solicitudes(solicitudes):
    # Sobrescribe el archivo CSV de solicitudes con la lista de datos actualizada
    with open(SOLICITUDES_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=SOLICITUD_FIELDS)
        w.writeheader()
        w.writerows(solicitudes)


# ── Autenticación ─────────────────────────────────────────────────────────────

def validar_login(usuario_input, contrasena_input):
    # Compara las credenciales ingresadas con los registros de usuarios del CSV
    for u in cargar_usuarios():
        if u['usuario'] == usuario_input and u['contrasena'] == contrasena_input:
            return u
    return None


def obtener_usuario(usuario_id):
    # Busca un usuario específico en la base de datos a través de su ID
    return next((u for u in cargar_usuarios() if u['id'] == usuario_id), None)


# ── Validación ────────────────────────────────────────────────────────────────

def parsear_fecha(fecha_str):
    # Convierte un texto con formato YYYY-MM-DD en un objeto de tipo fecha válido
    try:
        return datetime.strptime(fecha_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def calcular_dias(fecha_inicio, fecha_fin):
    # Calcula la cantidad total de días corridos entre dos fechas determinadas
    return (fecha_fin - fecha_inicio).days + 1


def validar_solicitud(empleado_id, fecha_inicio_str, fecha_fin_str):
    # Aplica todas las reglas de negocio sobre las fechas y saldos del empleado
    errores = []

    inicio = parsear_fecha(fecha_inicio_str)
    fin    = parsear_fecha(fecha_fin_str)

    if inicio is None:
        errores.append('Fecha de inicio inválida. Usá el formato YYYY-MM-DD.')
    if fin is None:
        errores.append('Fecha de fin inválida. Usá el formato YYYY-MM-DD.')
    if errores:
        return errores

    if inicio > fin:
        errores.append('La fecha de fin debe ser posterior a la fecha de inicio.')
        return errores

    if inicio.weekday() != 0:
        errores.append('La fecha de inicio debe ser un lunes.')

    dias = calcular_dias(inicio, fin)
    if dias % DIAS_BLOQUE != 0:
        errores.append(f'Las vacaciones deben pedirse en bloques de {DIAS_BLOQUE} días.')

    empleado = obtener_usuario(empleado_id)
    if empleado and int(empleado['dias_disponibles']) < dias:
        errores.append(
            f'Días insuficientes: disponibles {empleado["dias_disponibles"]}, solicitados {dias}.'
        )

    return errores


# ── Operaciones ───────────────────────────────────────────────────────────────

def registrar_solicitud(empleado_id, empleado_nombre, fecha_inicio_str, fecha_fin_str):
    # Genera un nuevo registro autoincremental de solicitud en estado pendiente inicial
    solicitudes = cargar_solicitudes()
    nuevo_id = str(max((int(s['id']) for s in solicitudes), default=0) + 1)
    inicio = parsear_fecha(fecha_inicio_str)
    fin    = parsear_fecha(fecha_fin_str)
    nueva = {
        'id':              nuevo_id,
        'empleado_id':     empleado_id,
        'empleado_nombre': empleado_nombre,
        'fecha_inicio':    fecha_inicio_str,
        'fecha_fin':       fecha_fin_str,
        'dias':            str(calcular_dias(inicio, fin)),
        'estado':          'PENDIENTE_PREAPROBACION',
        'fecha_solicitud': date.today().isoformat(),
        'comentario':      '',
    }
    solicitudes.append(nueva)
    guardar_solicitudes(solicitudes)
    return nueva


def preaprobar_solicitud(solicitud_id):
    # Cambia el estado para derivar la solicitud desde Jefatura hacia el área de RRHH
    solicitudes = cargar_solicitudes()
    for s in solicitudes:
        if s['id'] == solicitud_id:
            s['estado'] = 'PENDIENTE_APROBACION'
            guardar_solicitudes(solicitudes)
            return s
    return None


def aprobar_solicitud(solicitud_id):
    # Consolida la aprobación final y descuenta los días correspondientes del saldo del usuario
    solicitudes = cargar_solicitudes()
    for s in solicitudes:
        if s['id'] == solicitud_id:
            s['estado'] = 'APROBADA'
            guardar_solicitudes(solicitudes)
            usuarios = cargar_usuarios()
            for u in usuarios:
                if u['id'] == s['empleado_id']:
                    u['dias_disponibles'] = str(int(u['dias_disponibles']) - int(s['dias']))
                    guardar_usuarios(usuarios)
                    break
            return s
    return None


def rechazar_solicitud(solicitud_id, comentario=''):
    # Cancela la solicitud guardando opcionalmente el motivo especificado por el evaluador
    solicitudes = cargar_solicitudes()
    for s in solicitudes:
        if s['id'] == solicitud_id:
            s['estado'] = 'RECHAZADA'
            s['comentario'] = comentario
            guardar_solicitudes(solicitudes)
            return s
    return None


# ── Consultas ─────────────────────────────────────────────────────────────────

def obtener_solicitudes_por_estado(estado):
    # Filtra y extrae todas las solicitudes de la base de datos según el estado requerido
    return [s for s in cargar_solicitudes() if s['estado'] == estado]


def obtener_solicitudes_por_empleado(empleado_id):
    # Filtra y extrae todo el historial de solicitudes asociadas a un empleado en particular
    return [s for s in cargar_solicitudes() if s['empleado_id'] == empleado_id]
