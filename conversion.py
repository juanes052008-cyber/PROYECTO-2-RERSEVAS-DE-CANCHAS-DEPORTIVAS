"""Funciones de conversión de texto a tipos, compartidas por consola y GUI."""

from datetime import date


def convertir_fecha(texto):
    """Convierte 'AAAA-MM-DD' a date. Lanza ValueError si el formato o la fecha no son válidos."""
    try:
        return date.fromisoformat(str(texto).strip())
    except ValueError:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD y existir en el calendario.")


def convertir_decimal_positivo(texto):
    """Convierte texto a float > 0. Lanza ValueError si no es numérico o es <= 0."""
    try:
        valor = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError("Debe ingresar un número válido.")
    if not valor > 0 or valor == float("inf"):
        raise ValueError("El número debe ser mayor que cero.")
    return valor
