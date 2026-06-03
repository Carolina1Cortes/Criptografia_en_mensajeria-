import socket
import threading

HOST = '0.0.0.0' 
PORT = 5555
clientes = {}
# LISTA BLANCA: Solo el Admin puede entrar al inicio
usuarios_permitidos = {'Admin'} 

def manejar_cliente(conn, addr):
    nombre = conn.recv(1024).decode('utf-8')
    
    # 1. VERIFICACIÓN DE REGISTRO
    if nombre not in usuarios_permitidos:
        conn.send("Sistema|Acceso denegado. El Admin debe registrarte primero.".encode('utf-8'))
        conn.close()
        print(f"[RECHAZADO] {nombre} intentó conectar desde {addr} pero no está registrado.")
        return

    clientes[nombre] = conn
    print(f"[NUEVA CONEXIÓN] {nombre} conectado desde {addr}")

    while True:
        try:
            mensaje_recibido = conn.recv(1024).decode('utf-8')
            if not mensaje_recibido:
                break
            
            destinatario, texto = mensaje_recibido.split('|', 1)
            
            # 2. LÓGICA DE COMANDOS DEL ADMINISTRADOR
            if nombre == "Admin":
                if destinatario == "REGISTER":
                    usuarios_permitidos.add(texto)
                    conn.send(f"Sistema|Usuario '{texto}' añadido a la lista blanca.".encode('utf-8'))
                    print(f"[ADMIN] Registró al nuevo usuario: {texto}")
                    continue
                
                elif destinatario == "KICK":
                    if texto in clientes:
                        clientes[texto].send("Sistema|Has sido desconectado por el Administrador.".encode('utf-8'))
                        clientes[texto].close()
                        del clientes[texto]
                        conn.send(f"Sistema|El usuario {texto} fue expulsado.".encode('utf-8'))
                    else:
                        conn.send(f"Sistema|El usuario {texto} no está en línea.".encode('utf-8'))
                    continue
                
                elif destinatario == "KICKALL":
                    # Borramos a todos menos al Admin
                    usuarios_conectados = list(clientes.keys())
                    for u in usuarios_conectados:
                        if u != "Admin":
                            clientes[u].send("Sistema|El servidor ha cerrado todas las conexiones.".encode('utf-8'))
                            clientes[u].close()
                            del clientes[u]
                    conn.send("Sistema|Se ha expulsado a todos los usuarios.".encode('utf-8'))
                    print("[ADMIN] Expulsó a todos los clientes.")
                    continue

            # 3. LÓGICA DE MENSAJERÍA NORMAL (Clientes)
            if destinatario.upper() == "TODOS":
                print(f"[BROADCAST] De {nombre}: {texto}")
                for user, c_sock in clientes.items():
                    if user != nombre:
                        try: c_sock.send(f"{nombre} (Global)|{texto}".encode('utf-8'))
                        except: pass
            else:
                print(f"[INTERCEPTADO] De {nombre} para {destinatario}: {texto}")
                if destinatario in clientes:
                    clientes[destinatario].send(f"{nombre}|{texto}".encode('utf-8'))
                else:
                    conn.send(f"Sistema|El usuario {destinatario} no está conectado.".encode('utf-8'))
        except:
            break

    print(f"[DESCONEXIÓN] {nombre} se ha ido.")
    if nombre in clientes:
        del clientes[nombre]
    conn.close()

def iniciar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVIDOR ACTIVO] Escuchando en el puerto {PORT}...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()