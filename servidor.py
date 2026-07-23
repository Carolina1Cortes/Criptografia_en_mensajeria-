import socket
import threading

import protocolo

HOST = '0.0.0.0'
PORT = 5555
clientes = {}
# LISTA BLANCA: Solo el Admin puede entrar al inicio
usuarios_permitidos = {'Admin'}

# ================= FASE 2: ESTADO DE CIFRADO =================
# Modo global de cifrado activo: "PLANO", "DEBIL" o "RSA"
# El servidor NUNCA cifra ni descifra nada: solo reenvía bytes.
# El cifrado/descifrado ocurre siempre en el cliente (E2E real).
modo_cifrado = "PLANO"

# Directorio de claves públicas RSA: {nombre_usuario: "e,n"}
claves_publicas = {}


def manejar_cliente(conn, addr):
    global modo_cifrado

    buffer = protocolo.BufferRecepcion()
    try:
        nombre = buffer.recibir_mensaje(conn)
    except ConnectionError:
        return

    # 1. VERIFICACIÓN DE REGISTRO
    if nombre not in usuarios_permitidos:
        try:
            protocolo.enviar(conn, "Sistema|Acceso denegado. El Admin debe registrarte primero.")
        except Exception:
            pass
        conn.close()
        print(f"{addr[0]}:{addr[1]} rechazado (usuario no registrado: {nombre})")
        return

    clientes[nombre] = conn
    print(f"{addr[0]}:{addr[1]} conectado como {nombre}")

    # Le avisamos al recién conectado en qué modo de cifrado está el sistema
    # (por si se conecta después de que el Admin ya lo haya cambiado)
    try:
        protocolo.enviar(conn, f"SISTEMA_MODO|{modo_cifrado}")
    except Exception:
        pass

    while True:
        try:
            mensaje_recibido = buffer.recibir_mensaje(conn)

            destinatario, texto = mensaje_recibido.split('|', 1)

            # 2. DISTRIBUCIÓN DE CLAVES PÚBLICAS RSA (cualquier usuario)
            if destinatario == "__PUBKEY__":
                claves_publicas[nombre] = texto
                print(f"{nombre} actualizó su clave pública")

                # Avisamos a todos los demás de la nueva clave
                for user, c_sock in clientes.items():
                    if user != nombre:
                        try:
                            protocolo.enviar(c_sock, f"CLAVEPUB|{nombre}|{texto}")
                        except Exception:
                            pass

                # Y le enviamos al recién llegado el directorio completo existente
                for user, clave in claves_publicas.items():
                    if user != nombre:
                        try:
                            protocolo.enviar(conn, f"CLAVEPUB|{user}|{clave}")
                        except Exception:
                            pass
                continue

            # 3. LÓGICA DE COMANDOS DEL ADMINISTRADOR
            if nombre == "Admin":
                if destinatario == "REGISTER":
                    usuarios_permitidos.add(texto)
                    protocolo.enviar(conn, f"Sistema|Usuario '{texto}' añadido a la lista blanca.")
                    print(f"Usuario habilitado: {texto}")
                    continue

                elif destinatario == "KICK":
                    if texto in clientes:
                        protocolo.enviar(clientes[texto], "Sistema|Has sido desconectado por el Administrador.")
                        clientes[texto].close()
                        del clientes[texto]
                        protocolo.enviar(conn, f"Sistema|El usuario {texto} fue expulsado.")
                    else:
                        protocolo.enviar(conn, f"Sistema|El usuario {texto} no está en línea.")
                    continue

                elif destinatario == "KICKALL":
                    usuarios_conectados = list(clientes.keys())
                    for u in usuarios_conectados:
                        if u != "Admin":
                            protocolo.enviar(clientes[u], "Sistema|El servidor ha cerrado todas las conexiones.")
                            clientes[u].close()
                            del clientes[u]
                    protocolo.enviar(conn, "Sistema|Se ha expulsado a todos los usuarios.")
                    print("Todos los usuarios fueron desconectados")
                    continue

                elif destinatario == "CIFRADO":
                    # texto = "PLANO" | "DEBIL" | "RSA"
                    nuevo_modo = texto.strip().upper()
                    if nuevo_modo not in ("PLANO", "DEBIL", "RSA"):
                        protocolo.enviar(conn, f"Sistema|Modo de cifrado inválido: {texto}")
                        continue

                    modo_cifrado = nuevo_modo
                    for user, c_sock in clientes.items():
                        try:
                            protocolo.enviar(c_sock, f"SISTEMA_MODO|{modo_cifrado}")
                        except Exception:
                            pass
                    print(f"Modo de cifrado: {modo_cifrado}")
                    continue

            # 4. LÓGICA DE MENSAJERÍA NORMAL (Clientes)
            # NOTA: 'texto' aquí puede ser texto plano, cifrado débil (base64)
            # o cifrado RSA (números separados por comas), según el modo
            # elegido por cada emisor. El servidor lo trata como una caja
            # negra y solo lo reenvía -> esto es justamente lo que Wireshark
            # va a permitirles ver/comparar en cada modo.
            if destinatario.upper() == "TODOS":
                print(f"{nombre} -> TODOS: {texto}")
                for user, c_sock in clientes.items():
                    if user != nombre:
                        try:
                            protocolo.enviar(c_sock, f"{nombre} (Global)|{texto}")
                        except Exception:
                            pass
            else:
                print(f"{nombre} -> {destinatario}: {texto}")
                if destinatario in clientes:
                    protocolo.enviar(clientes[destinatario], f"{nombre}|{texto}")
                else:
                    protocolo.enviar(conn, f"Sistema|El usuario {destinatario} no está conectado.")
        except Exception:
            break

    print(f"{nombre} desconectado")
    if nombre in clientes:
        del clientes[nombre]
    conn.close()


def iniciar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Servidor escuchando en {HOST}:{PORT}")
    print(f"Modo de cifrado: {modo_cifrado}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    iniciar_servidor()
