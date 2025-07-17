# -*- coding: utf-8 -*-
"""
ARCHIVO DE INICIALIZACIÓN PRINCIPAL DEL MÓDULO CAPÍTULOS
========================================================

Este archivo es el punto de entrada principal del módulo de Odoo.
Se ejecuta cuando el módulo se carga y es responsable de importar
todos los subpaquetes y módulos necesarios.

ESTRUCTURA DE IMPORTACIONES:
1. models: Modelos de datos (ORM) - Backend
2. wizard: Asistentes para interacción con usuario
3. controllers: Controladores HTTP para endpoints web

FLUJO DE CARGA:
- Odoo lee este archivo al cargar el módulo
- Se importan todos los subpaquetes en orden
- Cada subpaquete tiene su propio __init__.py
- Los modelos se registran automáticamente en el ORM
- Los controladores se registran para rutas HTTP

REFERENCIAS:
- models/__init__.py: Importa todos los modelos de datos
- wizard/__init__.py: Importa el wizard de gestión de capítulos  
- controllers/__init__.py: Importa controladores HTTP/JSON
"""

# IMPORTACIÓN DE MODELOS DE DATOS (Backend Python)
# Contiene la lógica de negocio y estructura de datos
from . import models

# IMPORTACIÓN DE WIZARDS (Asistentes de Usuario)
# Contiene formularios interactivos para gestión de capítulos
from . import wizard

# IMPORTACIÓN DE CONTROLADORES HTTP
# Contiene endpoints web para comunicación JavaScript ↔ Python
from . import controllers
