<h1 align = "center">  
Criptografia en mensajeria </h1>
<p align="center">
  <img src="https://img.shields.io/badge/Estado-En Proceso-yellow" />
</p>

Sistema de Mensajería Cliente-Servidor (Fase 1: Texto Plano)

Este proyecto es la base para una aplicación de mensajería que implementará Cifrado de Extremo a Extremo basado en Matemáticas Discretas. En esta fase actual, el sistema funciona en texto plano (sin cifrado) a través de Sockets TCP en Python, permitiendo visualizar la vulnerabilidad de las redes antes de aplicar algoritmos criptográficos.

## 🛠️ Requisitos Previos

Python 3.x: Asegúrate de tener Python instalado en tu sistema.

Librerías: El proyecto utiliza socket, threading y tkinter. Todas vienen integradas por defecto en Python, por lo que NO necesitas instalar nada con pip.

Red (Opcional): Si vas a probarlo en varias computadoras, todas deben estar conectadas a la misma red WiFi/LAN.

## 📂 Archivos del Proyecto

servidor.py: El cerebro de la red. Enruta los mensajes y mantiene la lista blanca de usuarios.

admin.py: Panel de control exclusivo para el administrador del servidor.

cliente.py: Interfaz gráfica para los usuarios regulares (como Alice, Bob, Carolina, etc.).

## 🚀 Guía de Uso (Cómo no morir en el intento)

Para que el sistema funcione correctamente, el orden de ejecución es ESTRICTO. Sigue estos pasos:

#### Paso 1: Encender el Servidor
- Abre tu consola o terminal (CMD) y ejecuta:
  python servidor.py
- Nota: Verás un mensaje indicando que el servidor está escuchando en el puerto 5555. Déjalo abierto, esta consola será tu "monitor de espionaje" donde verás todo el tráfico en texto plano.

####  Paso 2: Conectar al Administrador
- Abre una nueva terminal y ejecuta:
python admin.py
- El Administrador se conectará automáticamente al servidor. El servidor inicia cerrado al público (Whitelist); nadie más puede entrar hasta que el Admin lo permita.

#### Paso 3: Registrar Usuarios (Lista Blanca)
Desde el panel de Administrador:

- En la casilla superior "Usuario a gestionar:", escribe el nombre del usuario que quieres permitir (ej. Alice).
- Haz clic en "Registrar (Permitir Ingreso)".
- Repite el proceso para los demás usuarios (ej. Bob, Carolina, Angel).

#### Paso 4: Conectar a los Clientes
- Por cada usuario que quieras simular, abre una nueva terminal y ejecuta:
python cliente.py
- Aparecerá una ventana pequeña pidiendo tu nombre.
- Ingresa exactamente el nombre que el Admin acaba de registrar (ej. Alice).
- Si escribes un nombre no registrado, el servidor rechazará la conexión y la app se cerrará sola.

## 💬 Cómo chatear

#### Para los Clientes:

- Mensaje Privado: En el panel izquierdo ("Destinatario:"), escribe el nombre exacto con quien quieres hablar (ej. Bob). Escribe tu mensaje abajo y presiona Enviar (o Enter).

- Mensaje Global: En el destinatario escribe la palabra mágica TODOS. Tu mensaje llegará a todos los usuarios conectados en ese momento.

#### Para el Administrador:

- Mensaje Global: Usa la barra inferior para enviar un anuncio a todo el servidor.

- Kick (Expulsar a uno): Escribe el nombre de un usuario en la barra superior y presiona "Expulsar Usuario".

- Kick All: Presiona el botón rojo "EXPULSAR A TODOS" para limpiar la sala y dejar el servidor vacío (solo quedará el Admin).

## ⚠️ Advertencia de Seguridad

ESTE SISTEMA NO ES SEGURO POR DISEÑO. (Para propósitos educativos)
Actualmente, cualquier tercero conectado a la red (un "ataque Eve") puede leer el tráfico interceptando los paquetes (usando herramientas como Wireshark) o simplemente mirando la consola del servidor. La siguiente fase del proyecto solucionará esta vulnerabilidad aplicando algoritmos de criptografía asimétrica (RSA) antes de enviar la información por los sockets.
