from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List
import uuid


class Mensaje:
    def __init__(self, remitente: str, destinatario: str, asunto: str, cuerpo: str):
        if not destinatario:
            raise ValueError("El mensaje debe tener destinatario.")
        self.__id = str(uuid.uuid4())
        self.__remitente = remitente
        self.__destinatario = destinatario
        self.__asunto = asunto
        self.__cuerpo = cuerpo
        self.__fecha = datetime.now()
        self.__leido = False

    @property
    def id(self) -> str:
        return self.__id

    @property
    def remitente(self) -> str:
        return self.__remitente

    @property
    def destinatario(self) -> str:
        return self.__destinatario

    @property
    def asunto(self) -> str:
        return self.__asunto

    @property
    def cuerpo(self) -> str:
        return self.__cuerpo

    @property
    def fecha(self) -> datetime:
        return self.__fecha

    @property
    def leido(self) -> bool:
        return self.__leido

    def marcar_leido(self) -> None:
        self.__leido = True

    def marcar_no_leido(self) -> None:
        self.__leido = False

    def __repr__(self) -> str:
        estado = "✓" if self.__leido else "•"
        return f"<Mensaje {estado} {self.__id[:8]} '{self.__asunto}'>"


class Carpeta:
    def __init__(self, nombre: str):
        self.__nombre = nombre
        self.__mensajes: List[Mensaje] = []

    @property
    def nombre(self) -> str:
        return self.__nombre

    def agregar_mensaje(self, mensaje: Mensaje) -> None:
        self.__mensajes.append(mensaje)

    def mensajes(self) -> List[Mensaje]:
        return list(self.__mensajes)

    def obtener_por_indice(self, idx: int) -> Mensaje | None:
        if 0 <= idx < len(self.__mensajes):
            return self.__mensajes[idx]
        return None

    def listar_mensajes(self, con_indices: bool = False) -> None:
        if not self.__mensajes:
            print("No hay mensajes.")
            return
        for i, m in enumerate(self.__mensajes, start=1):
            marca = "✓" if m.leido else "•"
            pref = f"{i}. " if con_indices else ""
            print(f"{pref}{marca} {m.fecha:%Y-%m-%d %H:%M} | De: {m.remitente} | Asunto: {m.asunto}|  Mensaje: {m.cuerpo}")


class Usuario:
    """Representa un usuario del sistema de correo, con sus carpetas y operaciones básicas."""
    def __init__(self, nombre: str, email: str):
        self.__nombre = nombre
        self.__email = email
        self.__carpetas: Dict[str, Carpeta] = {
            "Entrada": Carpeta("Entrada"),
            "Enviados": Carpeta("Enviados"),
        }

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre:
            raise ValueError("El nombre no puede ser vacío.")
        self.__nombre = nuevo_nombre

    @property
    def email(self) -> str:
        return self.__email

    def bandeja_entrada(self) -> Carpeta:
        return self.__carpetas["Entrada"]

    def carpeta_enviados(self) -> Carpeta:
        return self.__carpetas["Enviados"]

    def obtener_carpeta(self, nombre: str) -> Carpeta:
        if nombre not in self.__carpetas:
            self.__carpetas[nombre] = Carpeta(nombre)
        return self.__carpetas[nombre]

    def redactar(self, destinatario: str, asunto: str, cuerpo: str) -> Mensaje:
        return Mensaje(self.email, destinatario, asunto, cuerpo)

    def enviar_mensaje(self, servidor: "IMensajeria", destinatario: str, asunto: str, cuerpo: str) -> None:
        msg = self.redactar(destinatario, asunto, cuerpo)
        servidor.enviar(msg)

    def listar_mensajes(self) -> None:
        print(f"\nMensajes de {self.__nombre} (Entrada):")
        self.bandeja_entrada().listar_mensajes()

    def listar_enviados(self) -> None:
        print(f"\nMensajes de {self.__nombre} (Enviados):")
        self.carpeta_enviados().listar_mensajes()


class IMensajeria(ABC):
    @abstractmethod
    def enviar(self, m: Mensaje) -> None:
        raise NotImplementedError

    @abstractmethod
    def recibir(self, email: str) -> List[Mensaje]:
        raise NotImplementedError

    @abstractmethod
    def listar(self, email: str, carpeta: str) -> List[Mensaje]:
        raise NotImplementedError


class ServidorCorreo(IMensajeria):
    def __init__(self):
        self.__usuarios: Dict[str, Usuario] = {}

    def registrar_usuario(self, usuario: Usuario) -> None:
        if usuario.email in self.__usuarios:
            raise ValueError(f"Ya existe un usuario con email {usuario.email}")
        self.__usuarios[usuario.email] = usuario

    def _require_user(self, email: str) -> Usuario:
        u = self.__usuarios.get(email)
        if not u:
            raise ValueError(f"Usuario no registrado: {email}")
        return u

    def enviar(self, m: Mensaje) -> None:
        try:
            remitente = self._require_user(m.remitente)
            remitente.carpeta_enviados().agregar_mensaje(m)
        except ValueError:
            pass
        try:
            destinatario = self._require_user(m.destinatario)
            destinatario.bandeja_entrada().agregar_mensaje(m)
            print(f"Mensaje entregado a {destinatario.nombre}")
        except ValueError:
            print("Destinatario no encontrado en el servidor.")

    def recibir(self, email: str) -> List[Mensaje]:
        u = self._require_user(email)
        return u.bandeja_entrada().mensajes()

    def listar(self, email: str, carpeta: str) -> List[Mensaje]:
        u = self._require_user(email)
        return u.obtener_carpeta(carpeta).mensajes()


def seleccionar_carpeta(usuario: Usuario) -> Carpeta | None:
    print("\nSeleccionar carpeta:")
    print("1. Entrada")
    print("2. Enviados")
    elec = input("Opción: ").strip()
    if elec == "1":
        return usuario.bandeja_entrada()
    if elec == "2":
        return usuario.carpeta_enviados()
    print("Opción inválida.")
    return None


def menu(usuario: Usuario, servidor: ServidorCorreo) -> None:
    while True:
        print("\n--- MENÚ ---")
        print("1. Enviar mensaje")
        print("2. Ver bandeja de entrada")
        print("3. Ver enviados")
        print("4. Marcar como leído")
        print("5. Marcar como no leído")
        print("6. Cambiar nombre")
        print("7. Salir")

        opcion = input("Elegí una opción: ").strip()

        if opcion == "1":
            destinatario = input("Email del destinatario: ").strip()
            asunto = input("Asunto: ").strip()
            cuerpo = input("Mensaje: ").strip()
            usuario.enviar_mensaje(servidor, destinatario, asunto, cuerpo)

        elif opcion == "2":
            print()
            usuario.bandeja_entrada().listar_mensajes(con_indices=True)

        elif opcion == "3":
            print()
            usuario.carpeta_enviados().listar_mensajes(con_indices=True)

        elif opcion in {"4", "5"}:
            carpeta = seleccionar_carpeta(usuario)
            if carpeta is None:
                continue
            print()
            carpeta.listar_mensajes(con_indices=True)
            idx_txt = input("Número de mensaje: ").strip()
            if not idx_txt.isdigit():
                print("Índice inválido.")
                continue
            idx = int(idx_txt) - 1
            msg = carpeta.obtener_por_indice(idx)
            if not msg:
                print("Mensaje no encontrado.")
                continue
            if opcion == "4":
                msg.marcar_leido()
                print("Mensaje marcado como leído.")
            else:
                msg.marcar_no_leido()
                print("Mensaje marcado como no leído.")

        elif opcion == "6":
            nuevo_nombre = input("Nuevo nombre: ").strip()
            try:
                usuario.nombre = nuevo_nombre
                print("Nombre actualizado.")
            except ValueError as e:
                print(f"Error: {e}")

        elif opcion == "7":
            print("¡Hasta luego!")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    servidor = ServidorCorreo()

    usuario1 = Usuario("Luis", "luis@mail.com")
    usuario2 = Usuario("Ana", "ana@mail.com")

    servidor.registrar_usuario(usuario1)
    servidor.registrar_usuario(usuario2)

    menu(usuario1, servidor)

