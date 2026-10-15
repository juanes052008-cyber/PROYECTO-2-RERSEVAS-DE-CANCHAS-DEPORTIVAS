"""Pruebas T01 a T25. Ejecutar: python pruebas.py

Cada prueba declara condición inicial, entrada y resultado esperado; al correr
registra el resultado OBTENIDO real y lo guarda en resultados_pruebas.json.
Usa un "hoy" fijo (2026-10-14) para que no dependa de la fecha de ejecución.
"""

import json
import os
import sys
import tempfile
from datetime import date, timedelta

from errores import (ConflictoDisponibilidadError, DuplicadoError,
                     NoEncontradoError, OperacionNoPermitidaError)
from gestores import SistemaReservas
from repositorio import RepositorioJSON

HOY = date(2026, 10, 14)
F = date(2026, 10, 15)   # fecha de prueba
PRUEBAS = []


def prueba(id_, categoria, operacion, inicial, entrada, esperado):
    def deco(fn):
        PRUEBAS.append((id_, categoria, operacion, inicial, entrada, esperado, fn))
        return fn
    return deco


def sistema_base(con_canchas=True, con_clientes=True, ruta=None):
    s = SistemaReservas(RepositorioJSON(ruta) if ruta else None, hoy=HOY)
    if con_canchas:
        s.canchas.registrar_cancha("Cancha Fútbol 1", "FUTBOL", 80000)
        s.canchas.registrar_cancha("Vóley Playa 1", "VOLEY_PLAYA", 50000)
    if con_clientes:
        s.clientes.registrar_cliente("1001234567", "Ana Pérez", "3001234567")
        s.clientes.registrar_cliente("1098765432", "Luis Mora", "3109876543")
    return s


def lanza(tipo, fn, *args):
    try:
        fn(*args)
    except tipo as e:
        return e
    raise AssertionError(f"No se lanzó {tipo.__name__}")


@prueba("T01", "Registro válido", "O3", "Sin clientes.",
        'documento 1001234567, nombre "Ana Pérez", teléfono 3001234567',
        "Retorna Cliente CL001; clientes pasa de 0 a 1; JSON actualizado")
def t01():
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, "x.json")
        s = sistema_base(False, False, ruta)
        assert len(s.clientes.listar()) == 0
        c = s.clientes.registrar_cliente("1001234567", "Ana Pérez", "3001234567")
        s.guardar()
        assert c.obtener_id() == "CL001" and len(s.clientes.listar()) == 1
        datos = json.load(open(ruta, encoding="utf-8"))
        assert datos["clientes"][0]["documento"] == "1001234567"
        return "Cliente CL001 creado; clientes 0 -> 1; JSON contiene al cliente"


@prueba("T02", "Duplicado", "O3", "CL001 ya existe.",
        'Mismo documento con nombre "Otra Persona"',
        "DuplicadoError; clientes sigue en 1; CL001 sin cambios")
def t02():
    s = sistema_base(False, False)
    s.clientes.registrar_cliente("1001234567", "Ana Pérez", "3001234567")
    e = lanza(DuplicadoError, s.clientes.registrar_cliente, "1001234567", "Otra Persona", "3000000000")
    assert len(s.clientes.listar()) == 1
    assert s.clientes.buscar_por_id("CL001").obtener_nombre() == "Ana Pérez"
    return f"DuplicadoError ('{e}'); clientes = 1; CL001 sigue llamándose Ana Pérez"


@prueba("T03", "Registro válido", "O1", "Sin canchas.", '"Cancha Fútbol 1", FUTBOL, 80000',
        "Retorna Cancha C01; canchas pasa de 0 a 1")
def t03():
    s = sistema_base(False, False)
    assert len(s.canchas.listar()) == 0
    c = s.canchas.registrar_cancha("Cancha Fútbol 1", "FUTBOL", 80000)
    assert c.obtener_id() == "C01" and len(s.canchas.listar()) == 1
    return "Cancha C01 creada; canchas 0 -> 1"


@prueba("T04", "Dato inválido", "O1", "Sin canchas.",
        'Intentos: tipo "TENIS"; tarifa -5; tarifa "abc"; nombre " "',
        "Cada intento lanza ValueError con su mensaje; no se crea ninguna cancha")
def t04():
    s = sistema_base(False, False)
    msgs = []
    for args in (("Cancha X", "TENIS", 1000), ("Cancha X", "FUTBOL", -5),
                 ("Cancha X", "FUTBOL", "abc"), (" ", "FUTBOL", 1000)):
        msgs.append(str(lanza(ValueError, s.canchas.registrar_cancha, *args)))
    assert len(s.canchas.listar()) == 0
    return "4 ValueError (" + " / ".join(msgs) + "); canchas = 0"


@prueba("T05", "Dato inválido", "O3", "Sin clientes.",
        'Intentos: documento "12ab"; documento "123"; teléfono "300"; nombre vacío',
        "ValueError en cada caso; no se crea el cliente")
def t05():
    s = sistema_base(False, False)
    for args in (("12ab", "Ana", "3001234567"), ("123", "Ana", "3001234567"),
                 ("1001234567", "Ana", "300"), ("1001234567", "", "3001234567")):
        lanza(ValueError, s.clientes.registrar_cliente, *args)
    assert len(s.clientes.listar()) == 0
    return "4 ValueError; clientes = 0"


@prueba("T06", "Búsqueda inexistente", "O4", "Clientes CL001 y CL002.", "documento 999999999",
        'Retorna None; mensaje "No existe un cliente con el documento 999999999"; sin cambios')
def t06():
    s = sistema_base()
    r = s.clientes.buscar_por_documento("999999999")
    assert r is None and len(s.clientes.listar()) == 2
    return "Retorna None (la interfaz muestra: No existe un cliente con el documento 999999999); clientes = 2"


@prueba("T07", "Búsqueda inexistente", "O11", "Sin reservas.", 'id "R9999"',
        "Retorna None; mensaje de reserva no encontrada; sin cambios")
def t07():
    s = sistema_base()
    assert s.reservas.buscar_por_id("R9999") is None and not s.reservas.listar_todas()
    return "Retorna None; reservas = 0"


@prueba("T08", "Listas vacías", "O2, O5, O12", "Sistema sin canchas, clientes ni reservas.",
        "listar canchas, listar clientes, listar reservas",
        "Cada una retorna lista vacía sin error")
def t08():
    s = sistema_base(False, False)
    assert s.canchas.listar() == [] and s.clientes.listar() == [] and s.reservas.listar_todas() == []
    s2 = sistema_base()
    assert [c.obtener_id() for c in s2.canchas.listar("FUTBOL")] == ["C01"]
    return "Tres listas vacías; con canchas, el filtro FUTBOL retorna solo [C01]"


@prueba("T09", "Disponibilidad", "O8", "2 canchas, sin reservas.", "fecha 2026-10-15, sin tipo",
        "12 combinaciones libres (2 canchas × 6 franjas)")
def t09():
    s = sistema_base()
    n = len(s.reservas.consultar_disponibilidad(F))
    assert n == 12
    n2 = len(s.reservas.consultar_disponibilidad(F, "FUTBOL"))
    assert n2 == 6
    return f"{n} libres en total; {n2} libres con filtro FUTBOL"


@prueba("T10", "Reserva válida", "O9", "C01, CL001, sin reservas.", "CL001, C01, 2026-10-15, F3",
        "Reserva R0001 ACTIVA con costo 80000; reservas pasa de 0 a 1")
def t10():
    s = sistema_base()
    r = s.reservas.crear_reserva("CL001", "C01", F, "F3")
    assert r.obtener_id() == "R0001" and r.esta_activa() and r.obtener_costo() == 80000
    assert len(s.reservas.listar_todas()) == 1
    return f"{r.obtener_informacion()}"


@prueba("T11", "Conflicto", "O9", "R0001 ACTIVA (C01, 2026-10-15, F3).", "CL002, C01, 2026-10-15, F3",
        "ConflictoDisponibilidadError; reservas sigue en 1")
def t11():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    e = lanza(ConflictoDisponibilidadError, s.reservas.crear_reserva, "CL002", "C01", F, "F3")
    assert len(s.reservas.listar_todas()) == 1
    return f"ConflictoDisponibilidadError ('{e}'); reservas = 1"


@prueba("T12", "Referencia inexistente", "O9", "C01, CL001.",
        "cliente CL099; cancha C99; franja F9", "NoEncontradoError en cada caso; sin reservas nuevas")
def t12():
    s = sistema_base()
    lanza(NoEncontradoError, s.reservas.crear_reserva, "CL099", "C01", F, "F1")
    lanza(NoEncontradoError, s.reservas.crear_reserva, "CL001", "C99", F, "F1")
    lanza(NoEncontradoError, s.reservas.crear_reserva, "CL001", "C01", F, "F9")
    assert not s.reservas.listar_todas()
    return "3 NoEncontradoError; reservas = 0"


@prueba("T13", "Fecha fuera de rango", "O9", "Hoy = 2026-10-14.",
        "fechas 2026-10-13 (ayer) y 2026-11-14 (hoy+31)", "ValueError en ambas; sin reservas")
def t13():
    s = sistema_base()
    lanza(ValueError, s.reservas.crear_reserva, "CL001", "C01", HOY - timedelta(days=1), "F1")
    lanza(ValueError, s.reservas.crear_reserva, "CL001", "C01", HOY + timedelta(days=31), "F1")
    assert not s.reservas.listar_todas()
    return "2 ValueError; reservas = 0"


@prueba("T14", "Límites de fecha", "O9", "Hoy = 2026-10-14.",
        "fecha de hoy (2026-10-14) y hoy+30 (2026-11-13)", "Ambas se aceptan")
def t14():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", HOY, "F1")
    s.reservas.crear_reserva("CL001", "C01", HOY + timedelta(days=30), "F1")
    assert len(s.reservas.listar_todas()) == 2
    return "2 reservas creadas (límites incluidos)"


@prueba("T15", "Cancelación", "O10", "R0001 ACTIVA.", "cancelar R0001",
        "Estado CANCELADA; la reserva sigue en la colección")
def t15():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    s.reservas.cancelar_reserva("R0001")
    r = s.reservas.buscar_por_id("R0001")
    assert r is not None and r.obtener_estado() == "CANCELADA" and len(s.reservas.listar_todas()) == 1
    return "R0001 pasa a CANCELADA y se conserva (reservas = 1)"


@prueba("T16", "Reutilizar franja", "O10, O9", "R0001 CANCELADA (C01, 2026-10-15, F3).",
        "CL002 reserva C01, 2026-10-15, F3", "Se acepta: R0002 ACTIVA; las canceladas no ocupan")
def t16():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    s.reservas.cancelar_reserva("R0001")
    r = s.reservas.crear_reserva("CL002", "C01", F, "F3")
    assert r.obtener_id() == "R0002" and r.esta_activa()
    return "R0002 creada ACTIVA; R0001 sigue CANCELADA"


@prueba("T17", "Cancelar dos veces", "O10", "R0001 CANCELADA.", "cancelar R0001 otra vez",
        "OperacionNoPermitidaError; estado sin cambios")
def t17():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    s.reservas.cancelar_reserva("R0001")
    lanza(OperacionNoPermitidaError, s.reservas.cancelar_reserva, "R0001")
    assert s.reservas.buscar_por_id("R0001").obtener_estado() == "CANCELADA"
    return "OperacionNoPermitidaError; R0001 sigue CANCELADA"


@prueba("T18", "Cancelar inexistente", "O10", "Sin reservas.", 'cancelar "R9999"',
        "NoEncontradoError; sin cambios")
def t18():
    s = sistema_base()
    lanza(NoEncontradoError, s.reservas.cancelar_reserva, "R9999")
    return "NoEncontradoError"


@prueba("T19", "Eliminar válido", "O7", "CL002 sin reservas.", "eliminar documento 1098765432",
        "Cliente removido; clientes pasa de 2 a 1")
def t19():
    s = sistema_base()
    s.eliminar_cliente("1098765432")
    assert len(s.clientes.listar()) == 1 and s.clientes.buscar_por_documento("1098765432") is None
    return "CL002 eliminado; clientes 2 -> 1"


@prueba("T20", "Eliminar con reservas", "O7",
        "CL001 con una reserva CANCELADA y CL002 con una ACTIVA.", "eliminar ambos clientes",
        "OperacionNoPermitidaError en ambos; clientes sigue en 2")
def t20():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F1")
    s.reservas.cancelar_reserva("R0001")
    s.reservas.crear_reserva("CL002", "C01", F, "F2")
    lanza(OperacionNoPermitidaError, s.eliminar_cliente, "1001234567")
    lanza(OperacionNoPermitidaError, s.eliminar_cliente, "1098765432")
    lanza(NoEncontradoError, s.eliminar_cliente, "999999999")
    assert len(s.clientes.listar()) == 2
    return "2 OperacionNoPermitidaError (activa y cancelada); inexistente -> NoEncontradoError; clientes = 2"


@prueba("T21", "Actualización atómica", "O6", "CL001: Ana Pérez, 3001234567.",
        'nombre "Ana María" con teléfono "12" (inválido); luego nombre "Ana María" con teléfono 3112223344',
        "El primer intento lanza ValueError y NO cambia el nombre; el segundo actualiza ambos")
def t21():
    s = sistema_base()
    lanza(ValueError, s.clientes.actualizar_cliente, "1001234567", "Ana María", "12")
    c = s.clientes.buscar_por_documento("1001234567")
    assert c.obtener_nombre() == "Ana Pérez" and c.obtener_telefono() == "3001234567"
    s.clientes.actualizar_cliente("1001234567", "Ana María", "3112223344")
    assert c.obtener_nombre() == "Ana María" and c.obtener_telefono() == "3112223344"
    lanza(NoEncontradoError, s.clientes.actualizar_cliente, "999999999", "X", None)
    lanza(ValueError, s.clientes.actualizar_cliente, "1001234567", None, None)
    return "Intento inválido sin cambios; intento válido actualiza; inexistente y sin datos rechazados"


@prueba("T22", "Disponibilidad inválida", "O8", "Hoy = 2026-10-14.",
        "fecha 2026-12-31 (fuera de rango); disponibilidad tras crear R0001 (C01, F3)",
        "ValueError por fecha; con R0001 activa quedan 11 de 12 libres")
def t22():
    s = sistema_base()
    lanza(ValueError, s.reservas.consultar_disponibilidad, date(2026, 12, 31))
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    n = len(s.reservas.consultar_disponibilidad(F))
    assert n == 11
    s.reservas.cancelar_reserva("R0001")
    assert len(s.reservas.consultar_disponibilidad(F)) == 12
    return "ValueError; 11 libres con reserva activa; 12 al cancelarla"


@prueba("T23", "Filtros de reservas", "O12", "R0001 (CL001, 15-oct), R0002 (CL002, 15-oct), R0003 (CL001, 16-oct).",
        "listar por cliente CL001; por fecha 2026-10-15; por cliente sin reservas",
        "2 / 2 / lista vacía; orden por fecha y franja")
def t23():
    s = sistema_base()
    s.reservas.crear_reserva("CL001", "C01", F, "F3")
    s.reservas.crear_reserva("CL002", "C02", F, "F1")
    s.reservas.crear_reserva("CL001", "C01", F + timedelta(days=1), "F2")
    a = s.reservas.listar_por_cliente("CL001")
    b = s.reservas.listar_por_fecha(F)
    assert len(a) == 2 and len(b) == 2
    assert [r.obtener_id() for r in b] == ["R0002", "R0001"]   # F1 antes que F3
    assert s.reservas.listar_por_cliente("CL099") == []
    return "2 / 2 / []; la fecha 15-oct sale ordenada [R0002 (F1), R0001 (F3)]"


@prueba("T24", "Guardar y cargar", "O13, O14", "Sistema con 2 canchas, 2 clientes y 2 reservas (una cancelada).",
        "guardar en JSON; cargar en un sistema nuevo; crear una reserva más",
        "Mismos datos; relaciones restauradas; costo congelado; nuevo id R0003 (contadores recalculados)")
def t24():
    with tempfile.TemporaryDirectory() as d:
        ruta = os.path.join(d, "x.json")
        s = sistema_base(ruta=ruta)
        s.reservas.crear_reserva("CL001", "C01", F, "F3")
        s.reservas.crear_reserva("CL002", "C02", F, "F1")
        s.reservas.cancelar_reserva("R0002")
        s.guardar()
        n = SistemaReservas(RepositorioJSON(ruta), hoy=HOY)
        avisos = n.cargar()
        assert avisos == [] and len(n.canchas.listar()) == 2 and len(n.clientes.listar()) == 2
        r1, r2 = n.reservas.buscar_por_id("R0001"), n.reservas.buscar_por_id("R0002")
        assert r1.obtener_cliente().obtener_nombre() == "Ana Pérez" and r1.esta_activa()
        assert r2.obtener_estado() == "CANCELADA" and r1.obtener_costo() == 80000
        r3 = n.reservas.crear_reserva("CL001", "C01", F, "F4")
        assert r3.obtener_id() == "R0003"
        n.canchas.registrar_cancha("Nueva", "FUTBOL", 70000)
        assert n.canchas.buscar_por_id("C03") is not None
        assert not os.path.exists(ruta + ".tmp")
        # costo congelado si cambia la tarifa
        n.canchas.buscar_por_id("C01").actualizar_datos(tarifa=99000)
        assert n.reservas.buscar_por_id("R0001").obtener_costo() == 80000
        return "Datos idénticos tras cargar; R0003 nuevo; C03 nuevo; costo de R0001 sigue en 80000 tras subir la tarifa a 99000"


@prueba("T25", "Archivo con problemas", "O13",
        "datos_con_errores.json (reserva con cancha C99 y reserva activa duplicada); datos_corrupto.json; archivo inexistente.",
        "cargar cada archivo", "Omite y avisa los registros malos; el corrupto da sistema vacío con aviso y no se sobrescribe; sin archivo, 2 canchas de ejemplo")
def t25():
    base = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory() as d:
        import shutil
        for nombre in ("datos_con_errores.json", "datos_corrupto.json"):
            shutil.copy(os.path.join(base, nombre), d)
        s = SistemaReservas(RepositorioJSON(os.path.join(d, "datos_con_errores.json")), hoy=HOY)
        av = s.cargar()
        ids = [r.obtener_id() for r in s.reservas.listar_todas()]
        assert len(av) == 2 and "R0008" not in ids and "R0009" not in ids and len(ids) == 7
        original = open(os.path.join(d, "datos_corrupto.json")).read()
        c = SistemaReservas(RepositorioJSON(os.path.join(d, "datos_corrupto.json")), hoy=HOY)
        av2 = c.cargar()
        assert len(av2) == 1 and c.canchas.listar() == [] and c.clientes.listar() == []
        assert open(os.path.join(d, "datos_corrupto.json")).read() == original
        n = SistemaReservas(RepositorioJSON(os.path.join(d, "no_existe.json")), hoy=HOY)
        av3 = n.cargar()
        assert len(n.canchas.listar()) == 2 and len(av3) == 1
        return "Con errores: 2 avisos, 7 reservas válidas cargadas; corrupto: sistema vacío con 1 aviso y archivo intacto; sin archivo: 2 canchas de ejemplo"


def ejecutar_todas():
    resultados = []
    for id_, cat, op, ini, ent, esp, fn in PRUEBAS:
        try:
            obtenido, estado = fn(), "OK"
        except AssertionError as e:
            obtenido, estado = f"FALLÓ: {e}", "FALLA"
        except Exception as e:   # error no controlado = fallo
            obtenido, estado = f"ERROR NO CONTROLADO: {type(e).__name__}: {e}", "FALLA"
        resultados.append({"id": id_, "categoria": cat, "operacion": op, "inicial": ini,
                           "entrada": ent, "esperado": esp, "obtenido": obtenido, "estado": estado})
    return resultados


if __name__ == "__main__":
    res = ejecutar_todas()
    for r in res:
        print(f"{r['id']} [{r['estado']}] {r['categoria']}: {r['obtenido']}")
    ok = sum(r["estado"] == "OK" for r in res)
    print(f"\n{ok}/{len(res)} pruebas aprobadas")
    with open("resultados_pruebas.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    sys.exit(0 if ok == len(res) else 1)
