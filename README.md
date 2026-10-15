 Proyecto 2: Reservas de canchas deportivas

JUAN ESTEBAN SALDARRIAGA RAMIREZ 
JUAN JACOBO RODRÍGUEZ  
SAMUEL VALENCIA SANDOVAL 
SAMUEL DOMINGUEZ ARIZA

https://github.com/juanes052008-cyber/PROYECTO-2-RERSEVAS-DE-CANCHAS-DEPORTIVAS


## Requisitos

- Python 3.10 o superior.
- **Sin dependencias adicionales.** Solo se usa la biblioteca estándar (`json`, `datetime`, `tkinter`).
- `tkinter` viene con Python en Windows y macOS. En Linux puede requerir `sudo apt install python3-tk`.

## Estructura (por responsabilidades)

| Archivo | Capa | Contenido |
|---|---|---|
| `modelo.py` | Modelo | `Cancha`, `Cliente`, `FranjaHoraria`, `Reserva` y sus validaciones |
| `gestores.py` | Gestión | `GestorCanchas`, `GestorClientes`, `GestorReservas`, `SistemaReservas` (reglas de negocio) |
| `repositorio.py` | Almacenamiento | `RepositorioJSON` (guardado atómico, carga y reconstrucción de relaciones) |
| `errores.py` | Soporte | Excepciones propias |
| `conversion.py` | Interacción | `convertir_fecha`, `convertir_decimal_positivo` |
| `consola.py` | Interacción | Menú de consola (O1 a O15) |
| `interfaz.py` | Interacción | GUI Tkinter con pestañas |
| `pruebas.py` | Pruebas | Pruebas T01 a T25 con resultados obtenidos |

La lógica del negocio no depende de la interfaz: se prueba sin GUI.

## Ejecutar

Desde la carpeta del proyecto:

```bash
python consola.py                      # consola, usa datos_reservas.json
python interfaz.py                     # GUI, usa datos_reservas.json
python consola.py otra_ruta.json       # con otro archivo de datos
python pruebas.py                      # ejecuta T01-T25 y escribe resultados_pruebas.json
```

Los datos se cargan al iniciar y se guardan automáticamente después de cada cambio.

## Datos de demostración

- `datos_reservas.json`: 5 canchas (3 de fútbol, 2 de vóley playa), 6 clientes y 7 reservas (una cancelada) entre el 15 y el 20 de octubre de 2026. Para la demostración del 15 de octubre hay un conflicto posible: intente reservar **C01, 2026-10-15, F3** (ya ocupada por R0001).
- `datos_con_errores.json`: igual al anterior más una reserva con cancha inexistente (R0008) y una reserva activa duplicada (R0009). Al cargarlo se omiten y se avisan.
- `datos_corrupto.json`: JSON dañado. El sistema arranca vacío, avisa y deja una copia `.corrupto`.
- Si el archivo no existe, el sistema crea dos canchas de ejemplo.

Las fechas de reserva deben estar entre hoy y hoy + 30 días; si ejecuta después del 15 de octubre de 2026, use fechas actuales para crear reservas nuevas (las reservas de ejemplo siguen cargando sin problema).

## Demostración sugerida

1. Disponibilidad del 2026-10-15 (consola opción 8 o pestaña *Disponibilidad*).
2. Crear una reserva válida (cliente 1001234567, C03, 2026-10-15, F2).
3. Intentar el conflicto C01 / 2026-10-15 / F3 → se rechaza.
4. Cancelar R0001 y volver a reservar esa franja → se acepta.
5. Intentar eliminar a Ana Pérez (tiene reservas) → se rechaza.
6. Cerrar, volver a abrir y verificar que los datos persisten.
