"""Capa de gestión: colecciones y reglas del negocio.

No muestra mensajes, no lee JSON y no maneja widgets. Lanza excepciones
propias que la interfaz captura.
"""

from datetime import date, timedelta

from errores import (ConflictoDisponibilidadError, DuplicadoError,
                     NoEncontradoError, OperacionNoPermitidaError)
from modelo import (Cancha, Cliente, Reserva, crear_catalogo_franjas,
                    validar_tipo, validar_documento, validar_nombre)

DIAS_MAXIMOS_ANTICIPACION = 30


class GestorCanchas:
    """Administra la colección de canchas (dict id -> Cancha)."""

    def __init__(self):
        self.__canchas = {}
        self.__contador = 0

    def registrar_cancha(self, nombre, tipo, tarifa):
        # Se construye primero: si los datos son inválidos lanza ValueError
        # y no se consume ningún identificador.
        candidata = Cancha("TMP", nombre, tipo, tarifa)
        for c in self.__canchas.values():
            if c.obtener_nombre().lower() == candidata.obtener_nombre().lower():
                raise DuplicadoError(
                    f"Ya existe una cancha llamada '{c.obtener_nombre()}'.")
        self.__contador += 1
        cancha = Cancha(f"C{self.__contador:02d}", candidata.obtener_nombre(),
                        candidata.obtener_tipo(), candidata.obtener_tarifa())
        self.__canchas[cancha.obtener_id()] = cancha
        return cancha

    def agregar_existente(self, cancha):
        """Inserta una cancha ya construida (usado al cargar el JSON)."""
        self.__canchas[cancha.obtener_id()] = cancha
        self.__recalcular_contador()

    def buscar_por_id(self, id_cancha):
        return self.__canchas.get(id_cancha)

    def listar(self, tipo=None):
        if tipo is not None:
            tipo = validar_tipo(tipo)
        return [c for c in self.__canchas.values()
                if tipo is None or c.obtener_tipo() == tipo]

    def actualizar_cancha(self, id_cancha, nombre=None, tarifa=None):
        """Cambia nombre y/o tarifa de una cancha (el tipo no se modifica)."""
        cancha = self.buscar_por_id(id_cancha)
        if cancha is None:
            raise NoEncontradoError(f"No existe la cancha {id_cancha}.")
        if nombre is None and tarifa is None:
            raise ValueError("Debe indicar al menos un dato nuevo (nombre o tarifa).")
        if nombre is not None:
            nuevo = validar_nombre(nombre)
            for c in self.__canchas.values():
                if c is not cancha and c.obtener_nombre().lower() == nuevo.lower():
                    raise DuplicadoError(
                        f"Ya existe una cancha llamada '{c.obtener_nombre()}'.")
        cancha.actualizar_datos(nombre, tarifa)   # atómico
        return cancha

    def eliminar(self, id_cancha):
        if id_cancha not in self.__canchas:
            raise NoEncontradoError(f"No existe la cancha {id_cancha}.")
        del self.__canchas[id_cancha]

    def __recalcular_contador(self):
        numeros = [int(i[1:]) for i in self.__canchas if i[1:].isdigit()]
        self.__contador = max(numeros, default=0)


class GestorClientes:
    """Administra clientes y garantiza documentos únicos."""

    def __init__(self):
        self.__clientes = {}
        self.__contador = 0

    def registrar_cliente(self, documento, nombre, telefono):
        candidato = Cliente("TMP", documento, nombre, telefono)
        if self.buscar_por_documento(candidato.obtener_documento()) is not None:
            raise DuplicadoError(
                f"Ya existe un cliente con el documento {candidato.obtener_documento()}.")
        self.__contador += 1
        cliente = Cliente(f"CL{self.__contador:03d}", candidato.obtener_documento(),
                          candidato.obtener_nombre(), candidato.obtener_telefono())
        self.__clientes[cliente.obtener_id()] = cliente
        return cliente

    def agregar_existente(self, cliente):
        self.__clientes[cliente.obtener_id()] = cliente
        numeros = [int(i[2:]) for i in self.__clientes if i[2:].isdigit()]
        self.__contador = max(numeros, default=0)

    def buscar_por_documento(self, documento):
        documento = str(documento).strip()
        for c in self.__clientes.values():
            if c.obtener_documento() == documento:
                return c
        return None

    def buscar_por_id(self, id_cliente):
        return self.__clientes.get(id_cliente)

    def actualizar_cliente(self, documento, nombre=None, telefono=None):
        cliente = self.buscar_por_documento(documento)
        if cliente is None:
            raise NoEncontradoError(f"No existe un cliente con el documento {documento}.")
        if nombre is None and telefono is None:
            raise ValueError("Debe indicar al menos un dato nuevo (nombre o teléfono).")
        cliente.actualizar_datos(nombre, telefono)   # atómico
        return cliente

    def eliminar(self, id_cliente):
        if id_cliente not in self.__clientes:
            raise NoEncontradoError(f"No existe el cliente {id_cliente}.")
        del self.__clientes[id_cliente]

    def listar(self):
        return sorted(self.__clientes.values(), key=lambda c: c.obtener_id())


class GestorReservas:
    """Administra reservas, franjas y la regla de no conflicto."""

    def __init__(self, gestor_canchas, gestor_clientes, hoy=None):
        self.__reservas = {}
        self.__franjas = crear_catalogo_franjas()
        self.__gestor_canchas = gestor_canchas
        self.__gestor_clientes = gestor_clientes
        self.__contador = 0
        self.__hoy = hoy  # permite fijar "hoy" en las pruebas

    # ---- utilidades
    def hoy(self):
        return self.__hoy or date.today()

    def obtener_franjas(self):
        return list(self.__franjas)

    def buscar_franja(self, id_franja):
        for f in self.__franjas:
            if f.obtener_id() == id_franja:
                return f
        return None

    def validar_fecha(self, fecha):
        """Fecha válida: hoy <= fecha <= hoy + 30 días."""
        if not isinstance(fecha, date):
            raise ValueError("La fecha debe ser un objeto date.")
        hoy = self.hoy()
        limite = hoy + timedelta(days=DIAS_MAXIMOS_ANTICIPACION)
        if fecha < hoy or fecha > limite:
            raise ValueError(
                f"La fecha debe estar entre {hoy.isoformat()} y {limite.isoformat()}.")

    # ---- reglas
    def hay_conflicto(self, cancha, fecha, franja):
        return any(r.ocupa(cancha, fecha, franja) for r in self.__reservas.values())

    def crear_reserva(self, id_cliente, id_cancha, fecha, id_franja):
        cliente = self.__gestor_clientes.buscar_por_id(id_cliente)
        if cliente is None:
            raise NoEncontradoError(f"No existe el cliente {id_cliente}.")
        cancha = self.__gestor_canchas.buscar_por_id(id_cancha)
        if cancha is None:
            raise NoEncontradoError(f"No existe la cancha {id_cancha}.")
        franja = self.buscar_franja(id_franja)
        if franja is None:
            raise NoEncontradoError(f"No existe la franja {id_franja}.")
        self.validar_fecha(fecha)
        if self.hay_conflicto(cancha, fecha, franja):
            raise ConflictoDisponibilidadError(
                "La cancha ya está reservada en esa fecha y franja.")
        self.__contador += 1
        reserva = Reserva(f"R{self.__contador:04d}", cancha, cliente, fecha,
                          franja, costo=cancha.obtener_tarifa())
        self.__reservas[reserva.obtener_id()] = reserva
        return reserva

    def agregar_existente(self, reserva):
        """Inserta una reserva reconstruida (carga de JSON)."""
        self.__reservas[reserva.obtener_id()] = reserva
        numeros = [int(i[1:]) for i in self.__reservas if i[1:].isdigit()]
        self.__contador = max(numeros, default=0)

    def cancelar_reserva(self, id_reserva):
        reserva = self.buscar_por_id(id_reserva)
        if reserva is None:
            raise NoEncontradoError(f"No existe la reserva {id_reserva}.")
        reserva.cancelar()
        return reserva

    def consultar_disponibilidad(self, fecha, tipo=None):
        """Lista de (Cancha, Franja) libres para la fecha (y tipo opcional)."""
        self.validar_fecha(fecha)
        libres = []
        for cancha in self.__gestor_canchas.listar(tipo):
            for franja in self.__franjas:
                if not self.hay_conflicto(cancha, fecha, franja):
                    libres.append((cancha, franja))
        return libres

    # ---- consultas
    def buscar_por_id(self, id_reserva):
        return self.__reservas.get(id_reserva)

    def listar_todas(self):
        return self.__ordenar(self.__reservas.values())

    def listar_por_cliente(self, id_cliente):
        return self.__ordenar(r for r in self.__reservas.values()
                              if r.obtener_cliente().obtener_id() == id_cliente)

    def listar_por_fecha(self, fecha):
        return self.__ordenar(r for r in self.__reservas.values()
                              if r.obtener_fecha() == fecha)

    def cliente_tiene_reservas(self, id_cliente):
        return any(r.obtener_cliente().obtener_id() == id_cliente
                   for r in self.__reservas.values())

    def cancha_tiene_reservas(self, id_cancha):
        return any(r.obtener_cancha().obtener_id() == id_cancha
                   for r in self.__reservas.values())

    @staticmethod
    def __ordenar(reservas):
        return sorted(reservas, key=lambda r: (r.obtener_fecha(),
                                               r.obtener_franja().obtener_id(),
                                               r.obtener_id()))


class SistemaReservas:
    """Coordina gestores y almacenamiento; punto de entrada de la interfaz."""

    def __init__(self, repositorio=None, hoy=None):
        self.canchas = GestorCanchas()
        self.clientes = GestorClientes()
        self.reservas = GestorReservas(self.canchas, self.clientes, hoy)
        self.repositorio = repositorio

    def eliminar_cliente(self, documento):
        """Elimina un cliente sin reservas (ni activas ni canceladas)."""
        documento = validar_documento(documento) if documento else ""
        cliente = self.clientes.buscar_por_documento(documento)
        if cliente is None:
            raise NoEncontradoError(f"No existe un cliente con el documento {documento}.")
        if self.reservas.cliente_tiene_reservas(cliente.obtener_id()):
            raise OperacionNoPermitidaError(
                "El cliente tiene reservas (activas o canceladas) y no se puede eliminar.")
        self.clientes.eliminar(cliente.obtener_id())

    def eliminar_cancha(self, id_cancha):
        """Elimina una cancha sin reservas (ni activas ni canceladas)."""
        id_cancha = str(id_cancha).strip().upper()
        if self.canchas.buscar_por_id(id_cancha) is None:
            raise NoEncontradoError(f"No existe la cancha {id_cancha}.")
        if self.reservas.cancha_tiene_reservas(id_cancha):
            raise OperacionNoPermitidaError(
                "La cancha tiene reservas (activas o canceladas) y no se puede eliminar.")
        self.canchas.eliminar(id_cancha)

    def cargar(self):
        """Carga el JSON. Devuelve la lista de avisos."""
        if self.repositorio is None:
            return []
        return self.repositorio.cargar_en(self)

    def guardar(self):
        if self.repositorio is not None:
            self.repositorio.guardar(self.canchas.listar(),
                                     self.clientes.listar(),
                                     self.reservas.listar_todas())
