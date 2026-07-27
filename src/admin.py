import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import crypto_utils as cu
import protocolo


class AdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - Administrador")

        self.host = '127.0.0.1'
        self.port = 5555
        self.socket_admin = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ---- FASE 2: estado de cifrado ----
        self.modo_cifrado = "PLANO"          # se actualiza cuando el server confirme
        self.directorio_claves = {}          # {nombre: (e, n)} claves públicas de otros
        self.clave_publica = None
        self.clave_privada = None

        try:
            self.socket_admin.connect((self.host, self.port))
            # Nos identificamos como Admin automáticamente
            protocolo.enviar(self.socket_admin, "Admin")
        except Exception:
            messagebox.showerror("Error", "No se encontró el servidor.")
            self.root.destroy()
            return

        self.construir_interfaz()
        threading.Thread(target=self.recibir_mensajes, daemon=True).start()
        # Generamos nuestro propio par de claves RSA en segundo plano
        # (así están listas apenas alguien active el modo RSA)
        threading.Thread(target=self.generar_y_registrar_claves, daemon=True).start()

    # ------------------------------------------------------------------
    def generar_y_registrar_claves(self):
        self.clave_publica, self.clave_privada = cu.generar_claves_rsa(1024)
        try:
            texto_clave = cu.clave_publica_a_texto(self.clave_publica)
            protocolo.enviar(self.socket_admin, f"__PUBKEY__|{texto_clave}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    def construir_interfaz(self):
        # Panel de Controles
        frame_controles = tk.Frame(self.root, padx=10, pady=10, bg="#e0e0e0")
        frame_controles.pack(side=tk.TOP, fill=tk.X)

        tk.Label(frame_controles, text="Usuario a gestionar:", bg="#e0e0e0").grid(row=0, column=0, padx=5)
        self.entry_usuario = tk.Entry(frame_controles)
        self.entry_usuario.grid(row=0, column=1, padx=5)

        tk.Button(frame_controles, text="Registrar (Permitir Ingreso)", bg="#4CAF50", fg="white",
                  command=lambda: self.enviar_comando("REGISTER", self.entry_usuario.get())).grid(row=0, column=2, padx=5)

        tk.Button(frame_controles, text="Expulsar Usuario (Kick)", bg="#f44336", fg="white",
                  command=lambda: self.enviar_comando("KICK", self.entry_usuario.get())).grid(row=0, column=3, padx=5)

        tk.Button(frame_controles, text="EXPULSAR A TODOS", bg="#b71c1c", fg="white",
                  command=lambda: self.enviar_comando("KICKALL", "ALL")).grid(row=0, column=4, padx=20)

        # ---- FASE 2: Panel de cifrado ----
        frame_cifrado = tk.Frame(self.root, padx=10, pady=10, bg="#cfd8dc")
        frame_cifrado.pack(side=tk.TOP, fill=tk.X)

        tk.Label(frame_cifrado, text="Modo de cifrado global:", bg="#cfd8dc", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.combo_cifrado = ttk.Combobox(frame_cifrado, values=["PLANO", "DEBIL", "RSA"], state="readonly", width=10)
        self.combo_cifrado.set("PLANO")
        self.combo_cifrado.pack(side=tk.LEFT, padx=5)

        tk.Button(frame_cifrado, text="Aplicar a todo el servidor", bg="#1565c0", fg="white",
                  command=self.cambiar_cifrado).pack(side=tk.LEFT, padx=10)

        self.label_estado_cifrado = tk.Label(frame_cifrado, text="Estado actual: PLANO (sin cifrar)",
                                              bg="#cfd8dc", font=("Arial", 9, "italic"))
        self.label_estado_cifrado.pack(side=tk.LEFT, padx=20)

        # Panel de Chat Global
        frame_chat = tk.Frame(self.root, padx=10, pady=10)
        frame_chat.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.chat_area = tk.Text(frame_chat, state='disabled', bg="#333", fg="white", font=("Consolas", 10))
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        frame_input = tk.Frame(frame_chat)
        frame_input.pack(fill=tk.X)
        self.entry_mensaje = tk.Entry(frame_input, font=("Arial", 11))
        self.entry_mensaje.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(frame_input, text="Mensaje Global", command=self.enviar_global).pack(side=tk.RIGHT, padx=5)

    # ------------------------------------------------------------------
    def cambiar_cifrado(self):
        nuevo_modo = self.combo_cifrado.get()
        protocolo.enviar(self.socket_admin, f"CIFRADO|{nuevo_modo}")

    def enviar_comando(self, comando, objetivo):
        if objetivo:
            protocolo.enviar(self.socket_admin, f"{comando}|{objetivo}")
            self.entry_usuario.delete(0, tk.END)

    def enviar_global(self):
        mensaje = self.entry_mensaje.get()
        if not mensaje:
            return
        try:
            envios = cu.preparar_envios("TODOS", mensaje, self.modo_cifrado, self.directorio_claves)
        except ValueError as e:
            messagebox.showwarning("No se pudo cifrar", str(e))
            return

        for destinatario_real, payload in envios:
            protocolo.enviar(self.socket_admin, f"{destinatario_real}|{payload}")

        self.mostrar_log(f"Tú (a todos): {mensaje}")
        self.entry_mensaje.delete(0, tk.END)

    def mostrar_log(self, texto):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, texto + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    # ------------------------------------------------------------------
    def recibir_mensajes(self):
        buffer = protocolo.BufferRecepcion()
        while True:
            try:
                datos = buffer.recibir_mensaje(self.socket_admin)
                remitente, mensaje = datos.split('|', 1)

                if remitente == "SISTEMA_MODO":
                    self.modo_cifrado = mensaje.strip().upper()
                    etiqueta = {
                        "PLANO": "PLANO (sin cifrar)",
                        "DEBIL": "DEBIL (Cesar por bytes - rompible)",
                        "RSA": "RSA (asimétrico E2E)",
                    }.get(self.modo_cifrado, self.modo_cifrado)
                    self.label_estado_cifrado.config(text=f"Estado actual: {etiqueta}")
                    self.combo_cifrado.set(self.modo_cifrado)
                    self.mostrar_log(f"Modo de cifrado actualizado: {self.modo_cifrado}")
                    continue

                if remitente == "CLAVEPUB":
                    nombre_usuario, clave_texto = mensaje.split('|', 1)
                    self.directorio_claves[nombre_usuario] = cu.texto_a_clave_publica(clave_texto)
                    continue

                if remitente == "Sistema":
                    self.mostrar_log(mensaje)
                    continue

                # Mensaje de chat normal proveniente de un cliente -> descifrar
                texto_plano = cu.procesar_entrante(mensaje, self.modo_cifrado, self.clave_privada)
                self.mostrar_log(f"{remitente}: {texto_plano}")

            except Exception:
                self.socket_admin.close()
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminGUI(root)
    root.geometry("900x450")
    root.mainloop()
