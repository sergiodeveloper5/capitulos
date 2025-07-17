# -*- coding: utf-8 -*-
"""
==========================================
INICIALIZADOR DE MODELOS
==========================================

@file models/__init__.py
@description Inicializador del paquete de modelos de datos
@author Sergio Vadillo
@version 18.0.1.1.0
@since 2024

@overview
Este archivo importa todos los modelos de datos del módulo de capítulos
técnicos, asegurando que estén disponibles para el ORM de Odoo.

@models
- capitulo: Modelo principal para capítulos técnicos
- capitulo_seccion: Modelo para secciones dentro de capítulos
- sale_order: Extensión del modelo de pedidos de venta
- product_template: Extensión del modelo de plantillas de producto

@note
Los modelos se cargan automáticamente cuando se importa este paquete,
registrándose en el ORM para su uso en toda la aplicación.
"""

# Importación de todos los modelos del módulo
from . import capitulo           # Modelo principal de capítulos
from . import capitulo_seccion   # Modelo de secciones de capítulos
from . import sale_order         # Extensión de pedidos de venta
from . import product_template   # Extensión de plantillas de producto
