"""
crypto_utils.py
================
Módulo compartido de cifrado para el sistema de mensajería (Fase 2).

Contiene DOS familias de cifrado:

1) CIFRADO DEBIL (Cesar por bytes, clave fija de 1 byte -> 256 posibilidades)
   - Objetivo pedagógico: que sea "rompible" fácilmente por fuerza bruta,
     para demostrar con Wireshark + romper_cifrado.py que un cifrado con
     poco espacio de claves NO protege nada en la práctica.

2) RSA (implementado desde cero, sin librerías externas, usando
   Matemáticas Discretas: primalidad de Miller-Rabin, exponenciación
   modular, inverso modular).
   - Cada usuario genera su propio par de claves (pública/privada) al
     conectarse. La clave pública se distribuye a través del servidor
     (que actúa solo de "cartero", nunca ve la clave privada ni puede
     descifrar los mensajes -> cifrado de Extremo a Extremo real).

Este archivo debe estar en la MISMA carpeta que servidor.py, admin.py y
cliente.py, ya que los tres lo importan.
"""

import base64
import random

# =============================================================
#   1) CIFRADO DEBIL (para demostrar vulnerabilidad)
# =============================================================

CLAVE_DEBIL_POR_DEFECTO = 7  # desplazamiento fijo (0-255)


def cifrar_debil(texto: str, clave: int = CLAVE_DEBIL_POR_DEFECTO) -> str:
    """Cifra por desplazamiento fijo de bytes (tipo Cesar) y codifica en base64
    para poder enviarlo como texto por el socket."""
    datos = texto.encode("utf-8")
    cifrado = bytes([(b + clave) % 256 for b in datos])
    return base64.b64encode(cifrado).decode("ascii")


def descifrar_debil(texto_b64: str, clave: int = CLAVE_DEBIL_POR_DEFECTO) -> str:
    """Operación inversa a cifrar_debil."""
    cifrado = base64.b64decode(texto_b64.encode("ascii"))
    datos = bytes([(b - clave) % 256 for b in cifrado])
    return datos.decode("utf-8", errors="replace")


def romper_cifrado_debil(texto_b64: str) -> dict:
    """Fuerza bruta: prueba las 256 claves posibles y devuelve un diccionario
    {clave: texto_resultante}. Útil para el script romper_cifrado.py."""
    resultados = {}
    for clave in range(256):
        try:
            resultados[clave] = descifrar_debil(texto_b64, clave)
        except Exception:
            resultados[clave] = ""
    return resultados


# =============================================================
#   2) RSA (implementado desde cero)
# =============================================================

def _es_primo(n: int, k: int = 20) -> bool:
    """Test de primalidad de Miller-Rabin (probabilístico, k rondas)."""
    if n < 2:
        return False
    primos_pequenos = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in primos_pequenos:
        if n == p:
            return True
        if n % p == 0:
            return False

    # n - 1 = 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _generar_primo(bits: int) -> int:
    """Genera un número primo aleatorio de 'bits' bits."""
    while True:
        candidato = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if _es_primo(candidato):
            return candidato


def _mcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def generar_claves_rsa(bits: int = 1024):
    """Genera un par de claves RSA.

    bits: tamaño TOTAL del módulo n (se usan bits/2 para cada primo).
          1024 es razonable para la demo (tarda 1-3 seg en generarse
          y es, en la práctica, imposible de romper por fuerza bruta).
          Si quieren generación instantánea para pruebas, pueden bajarlo
          a 256, pero entonces SÍ sería rompible con recursos modestos
          (útil para otra demostración: "RSA débil por pocos bits").

    Devuelve: (clave_publica, clave_privada) donde cada una es (exponente, n)
    """
    mitad = bits // 2
    p = _generar_primo(mitad)
    q = _generar_primo(mitad)
    while q == p:
        q = _generar_primo(mitad)

    n = p * q
    phi = (p - 1) * (q - 1)

    e = 65537
    while _mcd(e, phi) != 1:
        e += 2

    d = pow(e, -1, phi)  # inverso modular (Python 3.8+)

    return (e, n), (d, n)


def _tam_bloque_bytes(n: int) -> int:
    """Cuántos bytes de texto plano caben de forma segura en un bloque,
    dado el módulo n (debe ser estrictamente menor que n)."""
    return max((n.bit_length() // 8) - 1, 1)


def rsa_cifrar(texto: str, clave_publica) -> str:
    """Cifra un texto (de cualquier longitud) partiéndolo en bloques."""
    e, n = clave_publica
    datos = texto.encode("utf-8")
    tam = _tam_bloque_bytes(n)
    bloques = [datos[i:i + tam] for i in range(0, len(datos), tam)] or [b""]

    cifrados = []
    for bloque in bloques:
        m = int.from_bytes(bloque, "big")
        c = pow(m, e, n)
        cifrados.append(str(c))
    return ",".join(cifrados)


def rsa_descifrar(texto_cifrado: str, clave_privada) -> str:
    """Descifra un texto cifrado con rsa_cifrar."""
    d, n = clave_privada
    datos = b""
    for bloque in texto_cifrado.split(","):
        if bloque == "":
            continue
        c = int(bloque)
        m = pow(c, d, n)
        tam_bytes = max((m.bit_length() + 7) // 8, 1)
        datos += m.to_bytes(tam_bytes, "big")
    return datos.decode("utf-8", errors="replace")


def clave_publica_a_texto(clave_publica) -> str:
    """Serializa (e, n) -> 'e,n' para enviar por el socket."""
    e, n = clave_publica
    return f"{e},{n}"


def texto_a_clave_publica(texto: str):
    """Deserializa 'e,n' -> (e, n)."""
    e_str, n_str = texto.split(",")
    return int(e_str), int(n_str)


# =============================================================
#   3) Helpers de alto nivel usados por admin.py / cliente.py
# =============================================================

def preparar_envios(destinatario: str, texto: str, modo: str, directorio_claves: dict):
    """
    Prepara el/los mensaje(s) listos para enviar por el socket, según el
    modo de cifrado activo.

    Devuelve una LISTA de tuplas (destinatario_real, payload_cifrado).
    Normalmente será una sola tupla, EXCEPTO en modo RSA + envío a "TODOS",
    donde no existe una única clave pública "de todos": en ese caso se
    cifra una copia distinta para cada contacto conocido (verdadero E2E,
    el servidor nunca ve el texto plano).
    """
    modo = (modo or "PLANO").upper()

    if modo == "DEBIL":
        return [(destinatario, cifrar_debil(texto))]

    if modo == "RSA":
        if destinatario.upper() == "TODOS":
            if not directorio_claves:
                raise ValueError("Aún no se conoce la clave pública de ningún contacto.")
            return [
                (nombre_dest, rsa_cifrar(texto, clave_pub))
                for nombre_dest, clave_pub in directorio_claves.items()
            ]
        else:
            if destinatario not in directorio_claves:
                raise ValueError(
                    f"No se conoce la clave pública de '{destinatario}' todavía."
                )
            return [(destinatario, rsa_cifrar(texto, directorio_claves[destinatario]))]

    # PLANO (o cualquier valor desconocido) -> sin cifrado
    return [(destinatario, texto)]


def procesar_entrante(payload: str, modo: str, clave_privada_propia):
    """Descifra un payload recibido según el modo de cifrado activo."""
    modo = (modo or "PLANO").upper()
    try:
        if modo == "DEBIL":
            return descifrar_debil(payload)
        if modo == "RSA":
            return rsa_descifrar(payload, clave_privada_propia)
        return payload
    except Exception:
        return "[No se pudo descifrar este mensaje]"
