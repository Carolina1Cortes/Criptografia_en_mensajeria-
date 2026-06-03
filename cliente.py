import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

class ClienteGUI:
    def __init__(self, root):
        self.root = root
        self.host = '127.0.0.1' 
        self.port = 5555
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.nombre = simpledialog.askstring("Login", "Tu nombre de usuario:")
        if not self.nombre:
            self.root.destroy()
            return
            
        self.root.title(f"Chat - {self.nombre}")

        try:
            self.socket_cliente.connect((self.host, self.port))
            self.socket_cliente.send(self.nombre.encode('utf-8'))
        except:
            messagebox.showerror("Error", "No se pudo conectar al servidor.")
            self.root.destroy()
            return

        self.construir_interfaz()
        threading.Thread(target=self.recibir_mensajes, daemon=True).start()

    def construir_interfaz(self):
        frame_izq = tk.Frame(self.root, width=150, bg="#e0e0e0")
        frame_izq.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(frame_izq, text="Destinatario:", bg="#e0e0e0").pack(pady=10)
        self.entry_destinatario = tk.Entry(frame_izq, font=("Arial", 10))
        self.entry_destinatario.pack(padx=10, pady=5)
        
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

    def enviar_mensaje(self):
        dest = self.entry_destinatario.get()
        msg = self.entry_mensaje.get()
        if dest and msg:
            self.socket_cliente.send(f"{dest}|{msg}".encode('utf-8'))
            self.mostrar_mensaje(f"[Tú -> {dest}]: {msg}")
            self.entry_mensaje.delete(0, tk.END)

    def recibir_mensajes(self):
        while True:
            try:
                datos = self.socket_cliente.recv(1024).decode('utf-8')
                if datos:
                    remitente, mensaje = datos.split('|', 1)
                    self.mostrar_mensaje(f"[{remitente}]: {mensaje}")
                else: raise Exception()
            except:
                self.mostrar_mensaje("\n[ALERTA]: Has sido desconectado.")
                self.socket_cliente.close()
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = ClienteGUI(root)
    root.geometry("600x400")
    root.mainloop()