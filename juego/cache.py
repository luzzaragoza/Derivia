"""Memorias de dibujos ya hechos (letras, fórmulas, islas, el gato...).

Dibujar es caro, así que cada pieza se guarda la primera vez y después se reusa. Todas se
registran acá para poder vaciarlas juntas cuando cambia la resolución de la pantalla (hay que
volver a dibujar todo al tamaño nuevo), y cada una tiene un tope: si se llena, se olvidan las
piezas más viejas en vez de crecer sin límite durante una sesión larga."""

import itertools


class CacheDibujos(dict):
    _todas = []

    def __init__(self, limite=None):
        super().__init__()
        self.limite = limite
        CacheDibujos._todas.append(self)

    def __setitem__(self, clave, valor):
        super().__setitem__(clave, valor)
        if self.limite and len(self) > self.limite:
            # los diccionarios recuerdan el orden en que se guardó: se va el cuarto más viejo
            for vieja in list(itertools.islice(iter(self), len(self) // 4)):
                del self[vieja]

    @classmethod
    def limpiar_todas(cls):
        for cache in cls._todas:
            cache.clear()
