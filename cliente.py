import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

import crypto_utils as cu
import protocolo


class ClienteGUI:
    def __init__(self, root):
        self.root = root
        self.host = '127.0.0.1'
        self.port = 5555
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ---- FASE 2: estado de cifrado ----
        self.modo_cifrado = "PLANO"
        self.directorio_claves = {}   # {nombre: (e, n)} claves públicas de otros
        self.clave_publica = None
        self.clave_privada = None

        self.nombre = simpledialog.askstring("Login", "Tu nombre de usuario:")
        if not self.nombre:
            self.root.destroy()
            return

        self.root.title(f"Chat - {self.nombre}")

        try:
            self.socket_cliente.connect((self.host, self.port))
            protocolo.enviar(self.socket_cliente, self.nombre)
        except Exception:
            messagebox.showerror("Error", "No se pudo conectar al servidor.")
            self.root.destroy()
            return

        self.construir_interfaz()
        threading.Thread(target=self.recibir_mensajes, daemon=True).start()
        threading.Thread(target=self.generar_y_registrar_claves, daemon=True).start()

    # ------------------------------------------------------------------
    def generar_y_registrar_claves(self):
        self.clave_publica, self.clave_privada = cu.generar_claves_rsa(1024)
        try:
            texto_clave = cu.clave_publica_a_texto(self.clave_publica)
            protocolo.enviar(self.socket_cliente, f"__PUBKEY__|{texto_clave}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    def construir_interfaz(self):
        frame_izq = tk.Frame(self.root, width=150, bg="#e0e0e0")
        frame_izq.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(frame_izq, text="Destinatario:", bg="#e0e0e0").pack(pady=10)
        self.entry_destinatario = tk.Entry(frame_izq, font=("Arial", 10))
        self.entry_destinatario.pack(padx=10, pady=5)

        self.label_modo = tk.Label(frame_izq, text="Cifrado:\nPLANO", bg="#e0e0e0", fg="#555", justify=tk.LEFT)
        self.label_modo.pack(pady=20, padx=10, anchor="w")

        frame_der = tk.Frame(self.root)
        frame_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.chat_area = tk.Text(frame_der, state='disabled', bg="#ffffff")
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        frame_input = tk.Frame(frame_der)
        frame_input.pack(fill=tk.X, padx=10, pady=5)
        self.entry_mensaje = tk.Entry(frame_input, font=("Arial", 11))
        self.entry_mensaje.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_mensaje.bind("<Return>", lambda event: self.enviar_mensaje())
        tk.Button(frame_input, text="Enviar", command=self.enviar_mensaje).pack(side=tk.RIGHT, padx=5)

    def mostrar_mensaje(self, texto):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, texto + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    # ------------------------------------------------------------------
    def enviar_mensaje(self):
        dest = self.entry_destinatario.get()
        msg = self.entry_mensaje.get()
        if not (dest and msg):
            return

        try:
            envios = cu.preparar_envios(dest, msg, self.modo_cifrado, self.directorio_claves)
        except ValueError as e:
            messagebox.showwarning("No se pudo cifrar", str(e))
            return

        for destinatario_real, payload in envios:
            protocolo.enviar(self.socket_cliente, f"{destinatario_real}|{payload}")

        self.mostrar_mensaje(f"Tú -> {dest}: {msg}")
        self.entry_mensaje.delete(0, tk.END)

    # ------------------------------------------------------------------
    def recibir_mensajes(self):
        buffer = protocolo.BufferRecepcion()
        while True:
            try:
                datos = buffer.recibir_mensaje(self.socket_cliente)
                remitente, mensaje = datos.split('|', 1)

                if remitente == "SISTEMA_MODO":
                    self.modo_cifrado = mensaje.strip().upper()
                    self.label_modo.config(text=f"Cifrado:\n{self.modo_cifrado}")
                    self.mostrar_mensaje(f"\nModo de cifrado actualizado: {self.modo_cifrado}")
                    continue

                if remitente == "CLAVEPUB":
                    nombre_usuario, clave_texto = mensaje.split('|', 1)
                    self.directorio_claves[nombre_usuario] = cu.texto_a_clave_publica(clave_texto)
                    continue

                if remitente == "Sistema":
                    self.mostrar_mensaje(mensaje)
                    continue

                # Mensaje de chat normal -> descifrar según el modo activo
                texto_plano = cu.procesar_entrante(mensaje, self.modo_cifrado, self.clave_privada)
                self.mostrar_mensaje(f"{remitente}: {texto_plano}")

            except Exception:
                self.mostrar_mensaje("\nHas sido desconectado.")
                self.socket_cliente.close()
                break


if __name__ == "__main__":
    root = tk.Tk()
    app = ClienteGUI(root)
    root.geometry("650x420")
    root.mainloop()
