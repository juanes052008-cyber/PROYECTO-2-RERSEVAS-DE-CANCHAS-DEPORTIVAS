"""Interfaz de consola (menú O1 a O15). Ejecutar: python consola.py [ruta.json]"""

import sys

from conversion import convertir_decimal_positivo, convertir_fecha
from errores import ReservasError
from repositorio import RepositorioJSON
from gestores import SistemaReservas

MENU = """
===== RESERVAS DE CANCHAS =====
 1. Registrar cancha            9. Crear reserva
 2. Listar canchas             10. Cancelar reserva
 3. Registrar cliente          11. Buscar reserva por id
 4. Buscar cliente             12. Listar reservas
 5. Listar clientes            13. Cargar datos (al iniciar)
 6. Actualizar cliente         14. Guardar datos ahora
 7. Eliminar cliente           15. Salir
 8. Consultar disponibilidad
"""


def confirmar(pregunta):
    return input(f"{pregunta} (Si/No): ").strip().lower() in ("si", "sí", "s")


def guardar(sistema):
    try:
        sistema.guardar()
    except OSError as e:
        print(f"AVISO: el cambio quedó en memoria pero no se pudo guardar ({e}).")


def mostrar(lista, vacio):
    if not lista:
        print(vacio)
    for x in lista:
        print("  ", x.obtener_informacion())


def ejecutar(sistema, op):
    if op == "1":
        c = sistema.canchas.registrar_cancha(
            input("Nombre: "), input("Tipo (FUTBOL / VOLEY_PLAYA): "),
            convertir_decimal_positivo(input("Tarifa por franja: ")))
        guardar(sistema)
        print("Cancha registrada:", c.obtener_informacion())
    elif op == "2":
        t = input("Tipo (Enter = todos): ").strip() or None
        mostrar(sistema.canchas.listar(t), "No hay canchas registradas.")
    elif op == "3":
        c = sistema.clientes.registrar_cliente(
            input("Documento: "), input("Nombre: "), input("Teléfono: "))
        guardar(sistema)
        print("Cliente registrado:", c.obtener_informacion())
    elif op == "4":
        c = sistema.clientes.buscar_por_documento(input("Documento: "))
        print(c.obtener_informacion() if c else "No existe un cliente con ese documento.")
    elif op == "5":
        mostrar(sistema.clientes.listar(), "No hay clientes registrados.")
    elif op == "6":
        doc = input("Documento del cliente: ")
        nombre = input("Nombre nuevo (Enter = sin cambio): ").strip() or None
        tel = input("Teléfono nuevo (Enter = sin cambio): ").strip() or None
        c = sistema.clientes.actualizar_cliente(doc, nombre, tel)
        guardar(sistema)
        print("Cliente actualizado:", c.obtener_informacion())
    elif op == "7":
        doc = input("Documento del cliente: ")
        c = sistema.clientes.buscar_por_documento(doc)
        if c is None:
            print("No existe un cliente con ese documento.")
        elif confirmar(f"¿Eliminar a {c.obtener_nombre()}?"):
            sistema.eliminar_cliente(doc)
            guardar(sistema)
            print("Cliente eliminado.")
        else:
            print("Operación cancelada; sin cambios.")
    elif op == "8":
        fecha = convertir_fecha(input("Fecha (AAAA-MM-DD): "))
        tipo = input("Tipo (Enter = todos): ").strip() or None
        libres = sistema.reservas.consultar_disponibilidad(fecha, tipo)
        if not libres:
            print("No hay franjas libres.")
        for cancha, franja in libres:
            print(f"   {cancha.obtener_id()} {cancha.obtener_nombre()} - {franja.obtener_id()} {franja.obtener_texto()}")
    elif op == "9":
        c = sistema.clientes.buscar_por_documento(input("Documento del cliente: "))
        if c is None:
            print("Cliente no registrado.")
            return
        r = sistema.reservas.crear_reserva(
            c.obtener_id(), input("Id de cancha (ej. C01): ").strip().upper(),
            convertir_fecha(input("Fecha (AAAA-MM-DD): ")),
            input("Franja (F1..F6): ").strip().upper())
        guardar(sistema)
        print("Reserva creada:", r.obtener_informacion())
    elif op == "10":
        r = sistema.reservas.buscar_por_id(input("Id de reserva: ").strip().upper())
        if r is None:
            print("No existe la reserva.")
        elif confirmar(f"¿Cancelar {r.obtener_informacion()}?"):
            sistema.reservas.cancelar_reserva(r.obtener_id())
            guardar(sistema)
            print("Reserva cancelada; la franja quedó disponible.")
        else:
            print("Operación cancelada; sin cambios.")
    elif op == "11":
        r = sistema.reservas.buscar_por_id(input("Id de reserva: ").strip().upper())
        print(r.obtener_informacion() if r else "No existe la reserva.")
    elif op == "12":
        modo = input("Filtro: [T]odas, [C]liente (documento), [F]echa: ").strip().upper()
        if modo == "C":
            c = sistema.clientes.buscar_por_documento(input("Documento: "))
            if c is None:
                print("No existe un cliente con ese documento.")
                return
            lista = sistema.reservas.listar_por_cliente(c.obtener_id())
        elif modo == "F":
            lista = sistema.reservas.listar_por_fecha(convertir_fecha(input("Fecha: ")))
        else:
            lista = sistema.reservas.listar_todas()
        mostrar(lista, "No hay reservas para ese criterio.")
    elif op == "13":
        print("Los datos se cargan automáticamente al iniciar. Para recargar, reinicie el programa.")
    elif op == "14":
        sistema.guardar()
        print("Datos guardados.")
    else:
        print("Opción no válida.")


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "datos_reservas.json"
    sistema = SistemaReservas(RepositorioJSON(ruta))
    for aviso in sistema.cargar():
        print("AVISO:", aviso)
    while True:
        print(MENU)
        op = input("Opción: ").strip()
        if op == "15":
            print("Hasta pronto.")
            break
        try:
            ejecutar(sistema, op)
        except ReservasError as e:
            print("ERROR:", e)
        except ValueError as e:
            print("DATO INVÁLIDO:", e)
        except OSError as e:
            print("ERROR DE ARCHIVO:", e)


if __name__ == "__main__":
    main()
