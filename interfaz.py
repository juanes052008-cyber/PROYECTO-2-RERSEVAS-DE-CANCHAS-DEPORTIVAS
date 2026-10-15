"""Interfaz gráfica (Tkinter) con pestañas: Reservas, Clientes, Canchas y Disponibilidad.

Solo muestra pantallas, lee datos, convierte texto a tipos e invoca al
SistemaReservas. No decide reglas del negocio. Ejecutar: python interfaz.py [ruta.json]
"""

import sys
import tkinter as tk
from tkinter import messagebox, ttk

from conversion import convertir_decimal_positivo, convertir_fecha
from errores import ReservasError
from gestores import SistemaReservas
from repositorio import RepositorioJSON


class InterfazGUI:
    def __init__(self, sistema):
        self.sistema = sistema
        self.ventana = tk.Tk()
        self.ventana.title("Reservas de Canchas")
        self.ventana.geometry("860x520")
        self.mensaje = tk.StringVar(value="Listo.")
        self.pestanas = ttk.Notebook(self.ventana)
        self.pestanas.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(self.ventana, textvariable=self.mensaje, anchor="w", relief="sunken",
                 bd=1).pack(fill="x", side="bottom")
        self._construir_reservas()
        self._construir_clientes()
        self._construir_canchas()
        self._construir_disponibilidad()
        self.refrescar_todo()

    # ----------------------------------------------------------- utilidades
    def mostrar_mensaje(self, texto):
        self.mensaje.set(texto)

    def _tabla(self, padre, columnas, anchos):
        arbol = ttk.Treeview(padre, columns=columnas, show="headings", height=10)
        for col, ancho in zip(columnas, anchos):
            arbol.heading(col, text=col)
            arbol.column(col, width=ancho, anchor="w")
        arbol.pack(fill="both", expand=True, padx=8, pady=8)
        return arbol

    def _guardar(self):
        try:
            self.sistema.guardar()
        except OSError as e:
            messagebox.showwarning("Guardado", f"El cambio existe en memoria pero no se pudo guardar:\n{e}")

    def _ejecutar(self, accion):
        """Ejecuta una acción y traduce los errores controlados a mensajes."""
        try:
            accion()
        except ReservasError as e:
            self.mostrar_mensaje(f"Error: {e}")
        except ValueError as e:
            self.mostrar_mensaje(f"Dato inválido: {e}")

    def refrescar_todo(self):
        self.refrescar_reservas()
        self.refrescar_clientes()
        self.refrescar_canchas()

    # ------------------------------------------------------------- reservas
    def _construir_reservas(self):
        f = ttk.Frame(self.pestanas)
        self.pestanas.add(f, text="Reservas")
        filtro = ttk.Frame(f)
        filtro.pack(fill="x", padx=8, pady=6)
        ttk.Label(filtro, text="Filtrar por documento:").pack(side="left")
        self.f_doc = ttk.Entry(filtro, width=14)
        self.f_doc.pack(side="left", padx=4)
        ttk.Label(filtro, text="por fecha (AAAA-MM-DD):").pack(side="left")
        self.f_fecha = ttk.Entry(filtro, width=12)
        self.f_fecha.pack(side="left", padx=4)
        ttk.Button(filtro, text="Buscar", command=lambda: self._ejecutar(self.refrescar_reservas)).pack(side="left", padx=4)
        ttk.Button(filtro, text="Ver todas", command=self._ver_todas).pack(side="left")
        self.t_reservas = self._tabla(
            f, ("Id", "Cliente", "Cancha", "Fecha", "Franja", "Estado", "Costo"),
            (70, 170, 150, 90, 90, 90, 80))
        botones = ttk.Frame(f)
        botones.pack(fill="x", padx=8, pady=6)
        ttk.Button(botones, text="Nueva reserva", command=lambda: self.manejar_reservar()).pack(side="left", padx=4)
        ttk.Button(botones, text="Cancelar reserva seleccionada", command=self.manejar_cancelar).pack(side="left", padx=4)
        ttk.Button(botones, text="Actualizar lista", command=self._ver_todas).pack(side="left", padx=4)

    def _ver_todas(self):
        self.f_doc.delete(0, "end")
        self.f_fecha.delete(0, "end")
        self.refrescar_reservas()

    def refrescar_reservas(self):
        doc, fecha = self.f_doc.get().strip(), self.f_fecha.get().strip()
        if doc:
            cliente = self.sistema.clientes.buscar_por_documento(doc)
            if cliente is None:
                self._llenar_reservas([])
                self.mostrar_mensaje("No existe un cliente con ese documento.")
                return
            lista = self.sistema.reservas.listar_por_cliente(cliente.obtener_id())
        elif fecha:
            lista = self.sistema.reservas.listar_por_fecha(convertir_fecha(fecha))
        else:
            lista = self.sistema.reservas.listar_todas()
        self._llenar_reservas(lista)
        if not lista:
            self.mostrar_mensaje("No hay reservas para ese criterio.")

    def _llenar_reservas(self, lista):
        self.t_reservas.delete(*self.t_reservas.get_children())
        for r in lista:
            self.t_reservas.insert("", "end", values=(
                r.obtener_id(), r.obtener_cliente().obtener_nombre(),
                r.obtener_cancha().obtener_nombre(), r.obtener_fecha().isoformat(),
                r.obtener_franja().obtener_texto(), r.obtener_estado(),
                f"{r.obtener_costo():,.0f}".replace(",", ".")))

    def manejar_reservar(self, id_cancha=None, fecha=None, id_franja=None):
        dlg = tk.Toplevel(self.ventana)
        dlg.title("Nueva reserva")
        dlg.transient(self.ventana)
        dlg.grab_set()
        canchas = self.sistema.canchas.listar()
        franjas = self.sistema.reservas.obtener_franjas()
        opciones_cancha = [f"{c.obtener_id()} - {c.obtener_nombre()}" for c in canchas]
        opciones_franja = [f"{f.obtener_id()} - {f.obtener_texto()}" for f in franjas]

        e_doc = ttk.Entry(dlg, width=20)
        e_fecha = ttk.Entry(dlg, width=20)
        cb_cancha = ttk.Combobox(dlg, values=opciones_cancha, state="readonly", width=30)
        cb_franja = ttk.Combobox(dlg, values=opciones_franja, state="readonly", width=30)
        lbl_cliente = ttk.Label(dlg, text="")
        lbl_costo = ttk.Label(dlg, text="Costo: -", font=("TkDefaultFont", 10, "bold"))
        lbl_msg = ttk.Label(dlg, text="", foreground="#b00020")

        for i, (txt, w) in enumerate([("Documento del cliente", e_doc), ("Cancha", cb_cancha),
                                      ("Fecha (AAAA-MM-DD)", e_fecha), ("Franja horaria", cb_franja)]):
            ttk.Label(dlg, text=txt).grid(row=i, column=0, sticky="w", padx=8, pady=4)
            w.grid(row=i, column=1, padx=8, pady=4)
        lbl_cliente.grid(row=0, column=2, padx=4)
        lbl_costo.grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        lbl_msg.grid(row=6, column=0, columnspan=3, sticky="w", padx=8)

        if id_cancha:
            cb_cancha.current([c.obtener_id() for c in canchas].index(id_cancha))
        if fecha:
            e_fecha.insert(0, fecha)
        if id_franja:
            cb_franja.current([f.obtener_id() for f in franjas].index(id_franja))

        def actualizar_costo(_evento=None):
            if cb_cancha.get():
                c = self.sistema.canchas.buscar_por_id(cb_cancha.get().split(" - ")[0])
                lbl_costo.config(text=f"Costo: ${c.obtener_tarifa():,.0f}".replace(",", "."))
        cb_cancha.bind("<<ComboboxSelected>>", actualizar_costo)
        actualizar_costo()

        def buscar_cliente():
            c = self.sistema.clientes.buscar_por_documento(e_doc.get())
            lbl_cliente.config(text=f"→ {c.obtener_nombre()} ({c.obtener_id()})" if c else "Cliente no registrado")

        def reservar():
            try:
                if not (e_doc.get().strip() and cb_cancha.get() and e_fecha.get().strip() and cb_franja.get()):
                    raise ValueError("Complete todos los campos.")
                f = convertir_fecha(e_fecha.get())
                cliente = self.sistema.clientes.buscar_por_documento(e_doc.get())
                if cliente is None:
                    raise ValueError("Cliente no registrado.")
                r = self.sistema.reservas.crear_reserva(
                    cliente.obtener_id(), cb_cancha.get().split(" - ")[0], f,
                    cb_franja.get().split(" - ")[0])
            except (ReservasError, ValueError) as e:
                lbl_msg.config(text=str(e))
                return
            self._guardar()
            self.refrescar_reservas()
            self.refrescar_disponibilidad_si_aplica()
            self.mostrar_mensaje(f"Reserva creada: {r.obtener_informacion()}")
            dlg.destroy()

        ttk.Button(dlg, text="Buscar cliente", command=buscar_cliente).grid(row=0, column=3, padx=4)
        ttk.Button(dlg, text="Reservar", command=reservar).grid(row=5, column=0, padx=8, pady=8)
        ttk.Button(dlg, text="Cerrar", command=dlg.destroy).grid(row=5, column=1, sticky="w", pady=8)

    def manejar_cancelar(self):
        sel = self.t_reservas.selection()
        if not sel:
            self.mostrar_mensaje("Seleccione una reserva de la tabla.")
            return
        id_reserva = self.t_reservas.item(sel[0])["values"][0]
        reserva = self.sistema.reservas.buscar_por_id(id_reserva)
        if reserva is None:
            self.mostrar_mensaje("No existe la reserva.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Cancelar esta reserva?\n\n{reserva.obtener_informacion()}"):
            self.mostrar_mensaje("Operación cancelada; sin cambios.")
            return

        def accion():
            self.sistema.reservas.cancelar_reserva(id_reserva)
            self._guardar()
            self.refrescar_reservas()
            self.mostrar_mensaje("Reserva cancelada; la franja quedó disponible.")
        self._ejecutar(accion)

    # -------------------------------------------------------------- clientes
    def _construir_clientes(self):
        f = ttk.Frame(self.pestanas)
        self.pestanas.add(f, text="Clientes")
        campos = ttk.Frame(f)
        campos.pack(fill="x", padx=8, pady=6)
        self.c_doc, self.c_nom, self.c_tel = (ttk.Entry(campos, width=w) for w in (16, 28, 14))
        for i, (txt, w) in enumerate([("Documento", self.c_doc), ("Nombre", self.c_nom), ("Teléfono", self.c_tel)]):
            ttk.Label(campos, text=txt).grid(row=0, column=i, sticky="w", padx=4)
            w.grid(row=1, column=i, padx=4)
        botones = ttk.Frame(f)
        botones.pack(fill="x", padx=8)
        for txt, accion in [("Registrar", "registrar"), ("Buscar por documento", "buscar"),
                            ("Actualizar", "actualizar"), ("Eliminar", "eliminar")]:
            ttk.Button(botones, text=txt, command=lambda a=accion: self.manejar_cliente(a)).pack(side="left", padx=4)
        self.t_clientes = self._tabla(f, ("Id", "Documento", "Nombre", "Teléfono"), (70, 140, 300, 140))
        self.t_clientes.bind("<<TreeviewSelect>>", self._seleccion_cliente)

    def _seleccion_cliente(self, _e):
        sel = self.t_clientes.selection()
        if sel:
            _, doc, nom, tel = self.t_clientes.item(sel[0])["values"]
            for entrada, valor in ((self.c_doc, doc), (self.c_nom, nom), (self.c_tel, tel)):
                entrada.delete(0, "end")
                entrada.insert(0, valor)

    def refrescar_clientes(self):
        self.t_clientes.delete(*self.t_clientes.get_children())
        lista = self.sistema.clientes.listar()
        for c in lista:
            self.t_clientes.insert("", "end", values=(c.obtener_id(), c.obtener_documento(),
                                                      c.obtener_nombre(), c.obtener_telefono()))
        if not lista:
            self.mostrar_mensaje("No hay clientes registrados.")

    def manejar_cliente(self, accion):
        doc, nom, tel = self.c_doc.get().strip(), self.c_nom.get().strip(), self.c_tel.get().strip()

        def ejecutar():
            if accion == "registrar":
                c = self.sistema.clientes.registrar_cliente(doc, nom, tel)
                self._guardar()
                self.mostrar_mensaje(f"Cliente registrado: {c.obtener_informacion()}")
            elif accion == "buscar":
                c = self.sistema.clientes.buscar_por_documento(doc)
                self.mostrar_mensaje(c.obtener_informacion() if c else f"No existe un cliente con el documento {doc}.")
            elif accion == "actualizar":
                c = self.sistema.clientes.actualizar_cliente(doc, nom or None, tel or None)
                self._guardar()
                self.mostrar_mensaje(f"Cliente actualizado: {c.obtener_informacion()}")
            elif accion == "eliminar":
                c = self.sistema.clientes.buscar_por_documento(doc)
                if c is None:
                    self.mostrar_mensaje(f"No existe un cliente con el documento {doc}.")
                elif messagebox.askyesno("Confirmar", f"¿Eliminar a {c.obtener_nombre()}?"):
                    self.sistema.eliminar_cliente(doc)
                    self._guardar()
                    self.mostrar_mensaje("Cliente eliminado.")
                else:
                    self.mostrar_mensaje("Operación cancelada; sin cambios.")
            self.refrescar_clientes()
        self._ejecutar(ejecutar)

    # --------------------------------------------------------------- canchas
    def _construir_canchas(self):
        f = ttk.Frame(self.pestanas)
        self.pestanas.add(f, text="Canchas")
        campos = ttk.Frame(f)
        campos.pack(fill="x", padx=8, pady=6)
        self.k_nom = ttk.Entry(campos, width=26)
        self.k_tipo = ttk.Combobox(campos, values=["FUTBOL", "VOLEY_PLAYA"], state="readonly", width=14)
        self.k_tipo.current(0)
        self.k_tarifa = ttk.Entry(campos, width=12)
        for i, (txt, w) in enumerate([("Nombre", self.k_nom), ("Tipo", self.k_tipo), ("Tarifa por franja", self.k_tarifa)]):
            ttk.Label(campos, text=txt).grid(row=0, column=i, sticky="w", padx=4)
            w.grid(row=1, column=i, padx=4)
        botones = ttk.Frame(f)
        botones.pack(fill="x", padx=8)
        ttk.Button(botones, text="Registrar cancha", command=self.manejar_cancha).pack(side="left", padx=4)
        ttk.Button(botones, text="Actualizar cancha", command=self.manejar_actualizar_cancha).pack(side="left", padx=4)
        ttk.Button(botones, text="Eliminar cancha", command=self.manejar_eliminar_cancha).pack(side="left", padx=4)
        ttk.Button(botones, text="Filtrar por tipo", command=lambda: self.refrescar_canchas(True)).pack(side="left", padx=4)
        ttk.Button(botones, text="Ver todas", command=self.refrescar_canchas).pack(side="left", padx=4)
        self.t_canchas = self._tabla(f, ("Id", "Nombre", "Tipo", "Tarifa"), (70, 260, 130, 110))
        self.t_canchas.bind("<<TreeviewSelect>>", self._seleccion_cancha)

    def _seleccion_cancha(self, _e):
        """Al elegir una fila, sus datos pasan a los campos para editarlos."""
        sel = self.t_canchas.selection()
        if sel:
            _, nom, tipo, tarifa = self.t_canchas.item(sel[0])["values"]
            self.k_nom.delete(0, "end")
            self.k_nom.insert(0, nom)
            self.k_tipo.set(tipo)
            self.k_tarifa.delete(0, "end")
            self.k_tarifa.insert(0, str(tarifa).replace(".", ""))

    def _cancha_seleccionada(self):
        sel = self.t_canchas.selection()
        if not sel:
            self.mostrar_mensaje("Seleccione una cancha de la tabla.")
            return None
        return self.t_canchas.item(sel[0])["values"][0]

    def manejar_actualizar_cancha(self):
        id_cancha = self._cancha_seleccionada()
        if id_cancha is None:
            return

        def ejecutar():
            nombre = self.k_nom.get().strip()
            tarifa_txt = self.k_tarifa.get().strip()
            if not nombre or not tarifa_txt:
                raise ValueError("Complete nombre y tarifa para actualizar.")
            c = self.sistema.canchas.actualizar_cancha(
                id_cancha, nombre, convertir_decimal_positivo(tarifa_txt))
            self._guardar()
            self.refrescar_canchas()
            self.refrescar_reservas()
            self.mostrar_mensaje(f"Cancha actualizada: {c.obtener_informacion()}")
        self._ejecutar(ejecutar)

    def manejar_eliminar_cancha(self):
        id_cancha = self._cancha_seleccionada()
        if id_cancha is None:
            return
        cancha = self.sistema.canchas.buscar_por_id(id_cancha)
        if cancha is None:
            self.mostrar_mensaje("No existe la cancha.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar la cancha?\n\n{cancha.obtener_informacion()}"):
            self.mostrar_mensaje("Operación cancelada; sin cambios.")
            return

        def ejecutar():
            self.sistema.eliminar_cancha(id_cancha)
            self._guardar()
            self.refrescar_canchas()
            self.mostrar_mensaje(f"Cancha {id_cancha} eliminada.")
        self._ejecutar(ejecutar)

    def refrescar_canchas(self, filtrar=False):
        """Lista las canchas; con filtrar=True solo las del tipo elegido."""
        self.t_canchas.delete(*self.t_canchas.get_children())
        lista = self.sistema.canchas.listar(self.k_tipo.get() if filtrar else None)
        for c in lista:
            self.t_canchas.insert("", "end", values=(c.obtener_id(), c.obtener_nombre(), c.obtener_tipo(),
                                                     f"{c.obtener_tarifa():,.0f}".replace(",", ".")))
        if not lista:
            self.mostrar_mensaje("No hay canchas registradas.")

    def manejar_cancha(self):
        def ejecutar():
            c = self.sistema.canchas.registrar_cancha(
                self.k_nom.get(), self.k_tipo.get(), convertir_decimal_positivo(self.k_tarifa.get()))
            self._guardar()
            self.refrescar_canchas()
            self.mostrar_mensaje(f"Cancha {c.obtener_id()} registrada.")
        self._ejecutar(ejecutar)

    # --------------------------------------------------------- disponibilidad
    def _construir_disponibilidad(self):
        f = ttk.Frame(self.pestanas)
        self.pestanas.add(f, text="Disponibilidad")
        campos = ttk.Frame(f)
        campos.pack(fill="x", padx=8, pady=6)
        ttk.Label(campos, text="Fecha (AAAA-MM-DD)").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(campos, text="Tipo (opcional)").grid(row=0, column=1, sticky="w", padx=4)
        self.d_fecha = ttk.Entry(campos, width=14)
        self.d_tipo = ttk.Combobox(campos, values=["Todos", "FUTBOL", "VOLEY_PLAYA"], state="readonly", width=14)
        self.d_tipo.current(0)
        self.d_fecha.grid(row=1, column=0, padx=4)
        self.d_tipo.grid(row=1, column=1, padx=4)
        ttk.Button(campos, text="Consultar", command=lambda: self._ejecutar(self.consultar_disponibilidad)).grid(row=1, column=2, padx=8)
        columnas = ["Cancha"] + [fr.obtener_texto() for fr in self.sistema.reservas.obtener_franjas()]
        self.t_disp = self._tabla(f, columnas, (220,) + (85,) * 6)
        self.t_disp.bind("<Double-1>", self._doble_clic_disponibilidad)
        ttk.Label(f, text="Doble clic en una franja Libre abre «Nueva reserva» con los datos elegidos.").pack(anchor="w", padx=8)

    def consultar_disponibilidad(self):
        fecha = convertir_fecha(self.d_fecha.get())
        tipo = None if self.d_tipo.get() == "Todos" else self.d_tipo.get()
        libres = {(c.obtener_id(), fr.obtener_id())
                  for c, fr in self.sistema.reservas.consultar_disponibilidad(fecha, tipo)}
        self.t_disp.delete(*self.t_disp.get_children())
        franjas = self.sistema.reservas.obtener_franjas()
        total = 0
        for c in self.sistema.canchas.listar(tipo):
            fila = [f"{c.obtener_id()} {c.obtener_nombre()}"]
            for fr in franjas:
                libre = (c.obtener_id(), fr.obtener_id()) in libres
                total += libre
                fila.append("Libre" if libre else "OCUPADA")
            self.t_disp.insert("", "end", iid=c.obtener_id(), values=fila)
        n = len(self.t_disp.get_children()) * len(franjas)
        self.mostrar_mensaje(f"{total} de {n} franjas libres." if total else "No hay franjas libres.")

    def refrescar_disponibilidad_si_aplica(self):
        if self.d_fecha.get().strip():
            try:
                self.consultar_disponibilidad()
            except (ReservasError, ValueError):
                pass

    def _doble_clic_disponibilidad(self, evento):
        fila = self.t_disp.identify_row(evento.y)
        col = self.t_disp.identify_column(evento.x)
        if not fila or col == "#1":
            return
        indice = int(col[1:]) - 2
        if self.t_disp.item(fila)["values"][indice + 1] == "Libre":
            self.manejar_reservar(fila, self.d_fecha.get().strip(), f"F{indice + 1}")

    # -------------------------------------------------------------- arranque
    def iniciar(self):
        self.ventana.mainloop()


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "datos_reservas.json"
    sistema = SistemaReservas(RepositorioJSON(ruta))
    avisos = sistema.cargar()
    gui = InterfazGUI(sistema)
    if avisos:
        gui.mostrar_mensaje(" | ".join(avisos))
    gui.iniciar()


if __name__ == "__main__":
    main()
