"""Capa de modelo: Cancha, Cliente, FranjaHoraria y Reserva.

Esta capa solo representa datos y los valida al crearse o actualizarse.
No lee teclado, no usa ventanas, no guarda archivos y no conoce otras
colecciones.
"""

from datetime import date

from errores import OperacionNoPermitidaError

TIPOS_CANCHA = ("FUTBOL", "VOLEY_PLAYA")
ESTADO_ACTIVA = "ACTIVA"
ESTADO_CANCELADA = "CANCELADA"


# ---------------------------------------------------------------- validaciones
def validar_nombre(nombre, campo="nombre"):
    """Devuelve el nombre sin espacios sobrantes o lanza ValueError."""
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(f"El {campo} no puede estar vacío.")
    return nombre.strip()


def validar_tipo(tipo):
    """Devuelve el tipo en mayúsculas o lanza ValueError si no es válido."""
    if not isinstance(tipo, str) or tipo.strip().upper() not in TIPOS_CANCHA:
        raise ValueError("El tipo debe ser FUTBOL o VOLEY_PLAYA.")
    return tipo.strip().upper()


def validar_tarifa(tarifa):
    """Devuelve la tarifa como float (> 0) o lanza ValueError."""
    if isinstance(tarifa, bool):
        raise ValueError("La tarifa debe ser un número mayor que cero.")
    try:
        valor = float(tarifa)
    except (TypeError, ValueError):
        raise ValueError("La tarifa debe ser un número mayor que cero.")
    if not valor > 0 or valor == float("inf"):
        raise ValueError("La tarifa debe ser un número mayor que cero.")
    return valor


def validar_documento(documento):
    """Documento: solo dígitos, de 5 a 12 caracteres."""
    doc = str(documento).strip() if documento is not None else ""
    if not (doc.isascii() and doc.isdigit() and 5 <= len(doc) <= 12):
        raise ValueError("El documento debe tener entre 5 y 12 dígitos.")
    return doc


def validar_telefono(telefono):
    """Teléfono: solo dígitos, de 7 a 10 caracteres."""
    tel = str(telefono).strip() if telefono is not None else ""
    if not (tel.isascii() and tel.isdigit() and 7 <= len(tel) <= 10):
        raise ValueError("El teléfono debe tener entre 7 y 10 dígitos.")
    return tel


# ---------------------------------------------------------------------- Cancha
class Cancha:
    """Cancha reservable con su tarifa por franja."""

    def __init__(self, id_cancha, nombre, tipo, tarifa):
        # Se valida todo antes de asignar: nunca queda un objeto a medias.
        nombre = validar_nombre(nombre)
        tipo = validar_tipo(tipo)
        tarifa = validar_tarifa(tarifa)
        self.__id_cancha = id_cancha
        self.__nombre = nombre
        self.__tipo = tipo
        self.__tarifa = tarifa

    def obtener_id(self):
        return self.__id_cancha

    def obtener_nombre(self):
        return self.__nombre

    def obtener_tipo(self):
        return self.__tipo

    def obtener_tarifa(self):
        return self.__tarifa

    def actualizar_datos(self, nombre=None, tarifa=None):
        """Cambia nombre y/o tarifa; valida antes de modificar."""
        nuevo_nombre = validar_nombre(nombre) if nombre is not None else self.__nombre
        nueva_tarifa = validar_tarifa(tarifa) if tarifa is not None else self.__tarifa
        self.__nombre = nuevo_nombre
        self.__tarifa = nueva_tarifa

    def a_diccionario(self):
        return {"id": self.__id_cancha, "nombre": self.__nombre,
                "tipo": self.__tipo, "tarifa": self.__tarifa}

    def obtener_informacion(self):
        return (f"{self.__id_cancha} | {self.__nombre} | {self.__tipo} | "
                f"Tarifa: ${self.__tarifa:,.0f}".replace(",", "."))


# --------------------------------------------------------------------- Cliente
class Cliente:
    """Cliente con sus datos de contacto."""

    def __init__(self, id_cliente, documento, nombre, telefono):
        documento = validar_documento(documento)
        nombre = validar_nombre(nombre)
        telefono = validar_telefono(telefono)
        self.__id_cliente = id_cliente
        self.__documento = documento
        self.__nombre = nombre
        self.__telefono = telefono

    def obtener_id(self):
        return self.__id_cliente

    def obtener_documento(self):
        return self.__documento

    def obtener_nombre(self):
        return self.__nombre

    def obtener_telefono(self):
        return self.__telefono

    def actualizar_datos(self, nombre=None, telefono=None):
        """Cambia nombre y/o teléfono. Valida todo antes de asignar."""
        nuevo_nombre = validar_nombre(nombre) if nombre is not None else self.__nombre
        nuevo_tel = validar_telefono(telefono) if telefono is not None else self.__telefono
        self.__nombre = nuevo_nombre
        self.__telefono = nuevo_tel

    def a_diccionario(self):
        return {"id": self.__id_cliente, "documento": self.__documento,
                "nombre": self.__nombre, "telefono": self.__telefono}

    def obtener_informacion(self):
        return (f"{self.__id_cliente} | Doc: {self.__documento} | "
                f"{self.__nombre} | Tel: {self.__telefono}")


# -------------------------------------------------------------- FranjaHoraria
class FranjaHoraria:
    """Franja predefinida del día (F1 a F6)."""

    def __init__(self, id_franja, hora_inicio, hora_fin):
        self.__id_franja = id_franja
        self.__hora_inicio = hora_inicio
        self.__hora_fin = hora_fin

    def obtener_id(self):
        return self.__id_franja

    def obtener_inicio(self):
        return self.__hora_inicio

    def obtener_fin(self):
        return self.__hora_fin

    def obtener_texto(self):
        return f"{self.__hora_inicio}-{self.__hora_fin}"


def crear_catalogo_franjas():
    """Catálogo fijo de seis franjas de una hora entre las 16:00 y las 22:00."""
    return [FranjaHoraria(f"F{i + 1}", f"{16 + i}:00", f"{17 + i}:00")
            for i in range(6)]


# --------------------------------------------------------------------- Reserva
class Reserva:
    """Une una cancha, un cliente, una fecha y una franja."""

    def __init__(self, id_reserva, cancha, cliente, fecha, franja,
                 estado=ESTADO_ACTIVA, costo=None):
        if not isinstance(fecha, date):
            raise ValueError("La fecha debe ser un objeto date.")
        if estado not in (ESTADO_ACTIVA, ESTADO_CANCELADA):
            raise ValueError("Estado de reserva inválido.")
        costo = cancha.obtener_tarifa() if costo is None else validar_tarifa(costo)
        self.__id_reserva = id_reserva
        self.__cancha = cancha
        self.__cliente = cliente
        self.__fecha = fecha
        self.__franja = franja
        self.__estado = estado
        self.__costo = costo   # se congela: no cambia si la tarifa cambia después

    def obtener_id(self):
        return self.__id_reserva

    def obtener_cancha(self):
        return self.__cancha

    def obtener_cliente(self):
        return self.__cliente

    def obtener_fecha(self):
        return self.__fecha

    def obtener_franja(self):
        return self.__franja

    def obtener_estado(self):
        return self.__estado

    def obtener_costo(self):
        return self.__costo

    def esta_activa(self):
        return self.__estado == ESTADO_ACTIVA

    def ocupa(self, cancha, fecha, franja):
        """True solo si está ACTIVA y coinciden cancha, fecha y franja."""
        return (self.esta_activa()
                and self.__cancha.obtener_id() == cancha.obtener_id()
                and self.__fecha == fecha
                and self.__franja.obtener_id() == franja.obtener_id())

    def cancelar(self):
        """ACTIVA -> CANCELADA. La reserva no se borra (queda el historial)."""
        if not self.esta_activa():
            raise OperacionNoPermitidaError(
                f"La reserva {self.__id_reserva} ya está cancelada.")
        self.__estado = ESTADO_CANCELADA

    def a_diccionario(self):
        return {"id": self.__id_reserva,
                "id_cancha": self.__cancha.obtener_id(),
                "id_cliente": self.__cliente.obtener_id(),
                "fecha": self.__fecha.isoformat(),
                "id_franja": self.__franja.obtener_id(),
                "estado": self.__estado,
                "costo": self.__costo}

    def obtener_informacion(self):
        return (f"{self.__id_reserva} | {self.__cliente.obtener_nombre()} | "
                f"{self.__cancha.obtener_nombre()} | {self.__fecha.isoformat()} | "
                f"{self.__franja.obtener_texto()} | {self.__estado} | "
                f"${self.__costo:,.0f}".replace(",", "."))
