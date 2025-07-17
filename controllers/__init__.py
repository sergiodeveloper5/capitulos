# -*- coding: utf-8 -*-
"""
==========================================
INICIALIZADOR DE CONTROLADORES
==========================================

@file controllers/__init__.py
@description Inicializador del paquete de controladores web
@author Sergio Vadillo
@version 18.0.1.1.0
@since 2024

@overview
Este archivo importa todos los controladores web del módulo de capítulos
técnicos, que manejan las peticiones HTTP y proporcionan endpoints
para la comunicación entre el frontend y el backend.

@controllers
- main: Controlador principal con endpoints para gestión de capítulos

@endpoints_provided
- /capitulos/search_products: Búsqueda de productos por categoría
- /capitulos/get_categories: Obtención de categorías de productos
- /capitulos/validate_data: Validación de datos de capítulos
- Otros endpoints específicos para operaciones CRUD

@note
Los controladores se registran automáticamente en el sistema de rutas
de Odoo cuando se importa este paquete.
"""

# Importación de todos los controladores del módulo
from . import main  # Controlador principal con endpoints de capítulos