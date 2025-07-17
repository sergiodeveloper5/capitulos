# -*- coding: utf-8 -*-
"""
INICIALIZACIÓN DEL PAQUETE CONTROLLERS
=====================================

Este archivo inicializa el paquete de controladores HTTP del módulo.
Los controladores manejan las peticiones web y proporcionan endpoints
para la comunicación entre JavaScript y Python.

CONTROLADORES INCLUIDOS:
- main.py: Controlador principal con endpoints JSON para:
  * Añadir productos a secciones
  * Búsqueda de productos
  * Validación de permisos

FUNCIONALIDAD:
- Endpoints HTTP/JSON para el widget JavaScript
- Comunicación bidireccional frontend ↔ backend
- Autenticación y autorización de usuarios
- Manejo de errores y logging

REFERENCIAS:
- main.py: CapitulosController con endpoints específicos
- static/src/js/capitulos_accordion_widget.js: Cliente JavaScript
"""

# IMPORTACIÓN DEL CONTROLADOR PRINCIPAL
# Contiene endpoints HTTP/JSON para comunicación con JavaScript
from . import main