"""Excepciones propias del sistema de reservas.

Las capas de modelo y gestión las lanzan; la interfaz las captura y
muestra el mensaje. Así la lógica se puede probar sin GUI.
"""


class ReservasError(Exception):
    """Clase base de los errores controlados del sistema."""


class DuplicadoError(ReservasError):
    """Se intentó registrar algo que ya existe (documento o nombre)."""


class NoEncontradoError(ReservasError):
    """No existe la entidad buscada por identificador o documento."""


class OperacionNoPermitidaError(ReservasError):
    """La operación no es válida en el estado actual."""


class ConflictoDisponibilidadError(ReservasError):
    """La cancha ya tiene una reserva ACTIVA en esa fecha y franja."""
