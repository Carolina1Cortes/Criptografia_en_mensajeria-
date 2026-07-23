"""
protocolo.py
============
TCP es un flujo de bytes: NO garantiza que cada recv() te entregue
exactamente un mensaje completo (puede entregarte medio mensaje, o
varios mensajes pegados). Esto no se nota con mensajes cortos en texto
plano, pero se vuelve un problema real con RSA, donde los mensajes son
mucho más largos (varios cientos de caracteres).

Este módulo agrega un delimitador ('\\n') al final de cada mensaje y
un buffer que reconstruye los mensajes completos sin importar cómo
lleguen los bytes.

Debe usarse SIEMPRE en vez de conn.send(...) / conn.recv(...) directos.
"""


def enviar(conn, texto: str) -> None:
    conn.sendall((texto + "\n").encode("utf-8"))


class BufferRecepcion:
    """Acumula bytes crudos de un socket y entrega mensajes completos,
    uno a la vez, sin importar cómo llegaron partidos/pegados por TCP."""

    def __init__(self):
        self._buffer = ""
        self._cola = []

    def _extraer_lineas(self):
        while "\n" in self._buffer:
            linea, self._buffer = self._buffer.split("\n", 1)
            if linea:
                self._cola.append(linea)

    def recibir_mensaje(self, conn, tam_lectura: int = 4096) -> str:
        """Bloquea hasta tener un mensaje completo disponible.
        Lanza ConnectionError si el socket se cerró."""
        while not self._cola:
            datos = conn.recv(tam_lectura)
            if not datos:
                raise ConnectionError("Conexión cerrada por el otro extremo.")
            self._buffer += datos.decode("utf-8", errors="replace")
            self._extraer_lineas()
        return self._cola.pop(0)
