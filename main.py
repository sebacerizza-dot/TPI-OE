import utils


# ── Presentación ──────────────────────────────────────────────────────────────

def sep():
    # Imprime una línea divisoria para organizar visualmente la consola
    print('-' * 55)


def mostrar_solicitud(s):
    # Traduce el estado técnico y muestra los datos formateados de una solicitud
    estado = utils.ESTADOS.get(s['estado'], s['estado'])
    print(f"  [{s['id']}] {s['empleado_nombre']:<20} "
          f"{s['fecha_inicio']} → {s['fecha_fin']}  "
          f"({s['dias']} días)  {estado}")
    if s['comentario']:
        print(f"       Motivo: {s['comentario']}")


def pedir_solicitud_de_lista(solicitudes):
    # Pide un ID por consola y busca esa solicitud dentro de la lista provista
    sol_id = input('ID a procesar (0 para volver): ').strip()
    if sol_id == '0':
        return None
    sol = next((s for s in solicitudes if s['id'] == sol_id), None)
    if not sol:
        print('ID no encontrado.')
    return sol


# ── Login ─────────────────────────────────────────────────────────────────────

def flujo_login():
    # Gestiona el acceso controlando el límite de intentos configurado
    for intento in range(1, utils.MAX_INTENTOS + 1):
        sep()
        print('      GESTOR DE VACACIONES')
        sep()
        usuario_input    = input('Usuario:    ').strip()
        contrasena_input = input('Contraseña: ').strip()
        usuario = utils.validar_login(usuario_input, contrasena_input)
        if usuario:
            return usuario
        restantes = utils.MAX_INTENTOS - intento
        if restantes > 0:
            print(f'Credenciales incorrectas. Intentos restantes: {restantes}.')
        else:
            print('Superó el límite de intentos. Acceso bloqueado.')
    return None


# ── Menú Empleado ─────────────────────────────────────────────────────────────

def menu_empleado(usuario):
    # Muestra las opciones del empleado y recarga sus datos en cada ciclo
    while True:
        u = utils.obtener_usuario(usuario['id'])
        sep()
        print(f'Bienvenido, {u["nombre"]}  |  Días disponibles: {u["dias_disponibles"]}')
        sep()
        print('1. Solicitar vacaciones')
        print('2. Ver días disponibles')
        print('3. Ver estado de mis solicitudes')
        print('0. Salir')
        opcion = input('Opción: ').strip()

        if opcion == '1':
            flujo_solicitar_vacaciones(u)
        elif opcion == '2':
            print(f'\nDías de vacaciones disponibles: {u["dias_disponibles"]}')
        elif opcion == '3':
            flujo_estado_solicitudes(u)
        elif opcion == '0':
            break
        else:
            print('Opción inválida.')


def flujo_solicitar_vacaciones(usuario):
    # Pide fechas, las valida con las reglas de negocio y registra la solicitud
    while True:
        sep()
        print('CONDICIONES DE SOLICITUD:')
        print('  - La fecha de inicio debe ser un lunes.')
        print('  - Las vacaciones se toman en bloques de 7 días.')
        print()
        fecha_inicio = input('Fecha inicio (YYYY-MM-DD) | 0 para cancelar: ').strip()
        if fecha_inicio == '0':
            return
        fecha_fin = input('Fecha fin    (YYYY-MM-DD): ').strip()

        errores = utils.validar_solicitud(usuario['id'], fecha_inicio, fecha_fin)
        if errores:
            print('\nSolicitud rechazada:')
            for e in errores:
                print(f'  • {e}')
            if input('\n¿Intentar de nuevo? (s/n): ').strip().lower() != 's':
                return
        else:
            sol = utils.registrar_solicitud(usuario['id'], usuario['nombre'], fecha_inicio, fecha_fin)
            print(f'\nSolicitud registrada (ID: {sol["id"]}). '
                  'Enviada a Jefatura para preaprobación.')
            return


def flujo_estado_solicitudes(usuario):
    # Obtiene y lista en pantalla el historial de solicitudes del empleado logueado
    solicitudes = utils.obtener_solicitudes_por_empleado(usuario['id'])
    if not solicitudes:
        print('\nNo tenés solicitudes registradas.')
        return
    sep()
    print('TUS SOLICITUDES:')
    for s in solicitudes:
        mostrar_solicitud(s)


# ── Menú Jefatura ─────────────────────────────────────────────────────────────

def menu_jefatura(usuario):
    # Despliega el panel de control exclusivo para los usuarios con rol Jefatura
    while True:
        sep()
        print(f'Bienvenido, {usuario["nombre"]}  (Jefatura)')
        sep()
        print('1. Ver solicitudes pendientes de preaprobación')
        print('0. Salir')
        opcion = input('Opción: ').strip()

        if opcion == '1':
            flujo_preaprobar()
        elif opcion == '0':
            break
        else:
            print('Opción inválida.')


def flujo_preaprobar():
    # Permite al jefe listar, seleccionar, preaprobar o rechazar solicitudes iniciales
    pendientes = utils.obtener_solicitudes_por_estado('PENDIENTE_PREAPROBACION')
    if not pendientes:
        print('\nNo hay solicitudes pendientes de preaprobación.')
        return
    sep()
    print('SOLICITUDES PENDIENTES DE PREAPROBACIÓN:')
    for s in pendientes:
        mostrar_solicitud(s)
    sep()
    sol = pedir_solicitud_de_lista(pendientes)
    if sol is None:
        return
    mostrar_solicitud(sol)
    if input('¿Preaprobar? (s/n): ').strip().lower() == 's':
        utils.preaprobar_solicitud(sol['id'])
        print('Solicitud preaprobada. Enviada a RRHH para aprobación final.')
    else:
        comentario = input('Motivo de rechazo: ').strip()
        utils.rechazar_solicitud(sol['id'], comentario)
        print('Solicitud rechazada. Notificación enviada al empleado.')


# ── Menú RRHH ─────────────────────────────────────────────────────────────────

def menu_rrhh(usuario):
    # Despliega el panel de control exclusivo para los usuarios con rol RRHH
    while True:
        sep()
        print(f'Bienvenido, {usuario["nombre"]}  (RRHH)')
        sep()
        print('1. Ver solicitudes pendientes de aprobación')
        print('0. Salir')
        opcion = input('Opción: ').strip()

        if opcion == '1':
            flujo_aprobar()
        elif opcion == '0':
            break
        else:
            print('Opción inválida.')


def flujo_aprobar():
    # Permite a RRHH auditar, otorgar la aprobación final o rechazar solicitudes
    pendientes = utils.obtener_solicitudes_por_estado('PENDIENTE_APROBACION')
    if not pendientes:
        print('\nNo hay solicitudes pendientes de aprobación.')
        return
    sep()
    print('SOLICITUDES PENDIENTES DE APROBACIÓN FINAL:')
    for s in pendientes:
        mostrar_solicitud(s)
    sep()
    sol = pedir_solicitud_de_lista(pendientes)
    if sol is None:
        return
    mostrar_solicitud(sol)
    if input('¿Aprobar? (s/n): ').strip().lower() == 's':
        utils.aprobar_solicitud(sol['id'])
        print('Solicitud aprobada. Días descontados del saldo del empleado.')
    else:
        comentario = input('Motivo de rechazo: ').strip()
        utils.rechazar_solicitud(sol['id'], comentario)
        print('Solicitud rechazada. Notificación enviada al empleado.')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Inicializa el flujo solicitando el login y deriva el control según el rol
    usuario = flujo_login()
    if not usuario:
        return

    rol = usuario['rol']
    if rol == 'empleado':
        menu_empleado(usuario)
    elif rol == 'jefatura':
        menu_jefatura(usuario)
    elif rol == 'rrhh':
        menu_rrhh(usuario)
    else:
        print(f'Rol "{rol}" no reconocido. Contactá a RRHH.')


if __name__ == '__main__':
    main()
