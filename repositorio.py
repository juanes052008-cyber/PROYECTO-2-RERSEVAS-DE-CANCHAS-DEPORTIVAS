"""Capa de almacenamiento: lectura y escritura del archivo JSON.

Convierte objetos a diccionarios y reconstruye las relaciones por
identificador. No aplica reglas de reservas ni conoce la GUI.
"""

import json
import os
import shutil
from datetime import date

from errores import ReservasError
from modelo import Cancha, Cliente, Reserva

VERSION_ARCHIVO = 1


class ArchivoCorruptoError(ReservasError):
    """El JSON no se puede interpretar."""


class RepositorioJSON:
    def __init__(self, ruta="datos_reservas.json"):
        self.ruta = ruta

    # ------------------------------------------------------------- guardado
    def guardar(self, canchas, clientes, reservas):
        """Escribe en un archivo temporal y luego lo reemplaza.

        Si algo falla se lanza OSError y el archivo anterior queda intacto.
        """
        datos = {
            "version": VERSION_ARCHIVO,
            "canchas": [c.a_diccionario() for c in canchas],
            "clientes": [c.a_diccionario() for c in clientes],
            "reservas": [r.a_diccionario() for r in reservas],
        }
        temporal = self.ruta + ".tmp"
        try:
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            os.replace(temporal, self.ruta)
        except OSError:
            if os.path.exists(temporal):
                try:
                    os.remove(temporal)
                except OSError:
                    pass
            raise

    # --------------------------------------------------------------- carga
    def existe(self):
        return os.path.exists(self.ruta)

    def cargar(self):
        """Lee el archivo y devuelve el diccionario con las tres listas."""
        try:
            with open(self.ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ArchivoCorruptoError(f"El archivo JSON está dañado: {e}")
        if not isinstance(datos, dict):
            raise ArchivoCorruptoError("El archivo JSON no tiene la estructura esperada.")
        for clave in ("canchas", "clientes", "reservas"):
            if not isinstance(datos.get(clave, []), list):
                raise ArchivoCorruptoError(f"La clave '{clave}' no es una lista.")
        return {"canchas": datos.get("canchas", []),
                "clientes": datos.get("clientes", []),
                "reservas": datos.get("reservas", [])}

    def reconstruir_reservas(self, datos, canchas, clientes, franjas):
        """Crea objetos Reserva a partir de identificadores.

        Devuelve (reservas, avisos). Omite y reporta los registros con
        referencias inexistentes, datos inválidos o conflictos.
        """
        reservas, avisos = [], []
        ocupadas = set()
        for reg in datos:
            try:
                id_res = reg["id"]
                cancha = canchas.get(reg["id_cancha"])
                cliente = clientes.get(reg["id_cliente"])
                franja = franjas.get(reg["id_franja"])
                if cancha is None or cliente is None or franja is None:
                    avisos.append(f"Reserva {id_res} omitida: referencia inexistente.")
                    continue
                fecha = date.fromisoformat(reg["fecha"])
                reserva = Reserva(id_res, cancha, cliente, fecha, franja,
                                  reg.get("estado", "ACTIVA"), reg.get("costo"))
            except (KeyError, TypeError, ValueError) as e:
                avisos.append(f"Registro de reserva omitido ({e}).")
                continue
            if reserva.esta_activa():
                clave = (cancha.obtener_id(), fecha, franja.obtener_id())
                if clave in ocupadas:
                    avisos.append(f"Reserva {id_res} omitida: conflicto con otra reserva activa.")
                    continue
                ocupadas.add(clave)
            reservas.append(reserva)
        return reservas, avisos

    def cargar_en(self, sistema):
        """Carga el archivo dentro de un SistemaReservas. Devuelve avisos."""
        avisos = []
        if not self.existe():
            # Sin archivo: dos canchas de ejemplo
            sistema.canchas.registrar_cancha("Cancha Futbol 1", "FUTBOL", 80000)
            sistema.canchas.registrar_cancha("Voley Playa 1", "VOLEY_PLAYA", 50000)
            return ["No existía el archivo de datos: se crearon dos canchas de ejemplo."]
        try:
            datos = self.cargar()
        except ArchivoCorruptoError as e:
            # No se sobrescribe: se conserva una copia del archivo dañado.
            copia = self.ruta + ".corrupto"
            try:
                shutil.copyfile(self.ruta, copia)
            except OSError:
                copia = "(no se pudo copiar)"
            return [f"{e} Se inició con el sistema vacío; copia del original en {copia}."]

        canchas, clientes = {}, {}
        for reg in datos["canchas"]:
            try:
                c = Cancha(reg["id"], reg["nombre"], reg["tipo"], reg["tarifa"])
                canchas[c.obtener_id()] = c
                sistema.canchas.agregar_existente(c)
            except (KeyError, TypeError, ValueError) as e:
                avisos.append(f"Cancha omitida ({e}).")
        docs = set()
        for reg in datos["clientes"]:
            try:
                cl = Cliente(reg["id"], reg["documento"], reg["nombre"], reg["telefono"])
                if cl.obtener_documento() in docs:
                    avisos.append(f"Cliente {cl.obtener_id()} omitido: documento repetido.")
                    continue
                docs.add(cl.obtener_documento())
                clientes[cl.obtener_id()] = cl
                sistema.clientes.agregar_existente(cl)
            except (KeyError, TypeError, ValueError) as e:
                avisos.append(f"Cliente omitido ({e}).")
        franjas = {f.obtener_id(): f for f in sistema.reservas.obtener_franjas()}
        reservas, av = self.reconstruir_reservas(datos["reservas"], canchas, clientes, franjas)
        avisos.extend(av)
        for r in reservas:
            sistema.reservas.agregar_existente(r)
        return avisos
