import socket
import threading
import tkinter as tk
from tkinter import messagebox

class AdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - Administrador")
        
        self.host = '127.0.0.1' 
        self.port = 5555
        self.socket_admin = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket_admin.connect((self.host, self.port))
            # Nos identificamos como Admin automáticamente
            self.socket_admin.send("Admin".encode('utf-8')) 
        except Exception as e:
            messagebox.showerror("Error", "No se encontró el servidor.")
            self.root.destroy()
            return

        self.construir_interfaz()
        threading.Thread(target=self.recibir_mensajes, daemon=True).start()

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

    def enviar_comando(self, comando, objetivo):
        if objetivo:
            self.socket_admin.send(f"{comando}|{objetivo}".encode('utf-8'))
            self.entry_usuario.delete(0, tk.END)

    def enviar_global(self):
        mensaje = self.entry_mensaje.get()
        if mensaje:
            self.socket_admin.send(f"TODOS|{mensaje}".encode('utf-8'))
            self.mostrar_log(f"[ADMIN -> TODOS]: {mensaje}")
            self.entry_mensaje.delete(0, tk.END)

    def mostrar_log(self, texto):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, texto + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def recibir_mensajes(self):
        while True:
            try:
                datos = self.socket_admin.recv(1024).decode('utf-8')
                if datos:
                    remitente, mensaje = datos.split('|', 1)
                    self.mostrar_log(f"[{remitente}]: {mensaje}")
            except:
                self.socket_admin.close()
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminGUI(root)
    root.geometry("800x400")
    root.mainloop()