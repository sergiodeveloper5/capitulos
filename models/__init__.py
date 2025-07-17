# -*- coding: utf-8 -*-
"""
INICIALIZACIÓN DEL PAQUETE MODELS
=================================

Este archivo inicializa todos los modelos de datos del módulo.
Los modelos definen la estructura de la base de datos y la lógica
de negocio del sistema de gestión de capítulos.

MODELOS INCLUIDOS:
1. capitulo.py: Modelo principal de capítulos técnicos
2. capitulo_seccion.py: Modelo de secciones dentro de capítulos
3. sale_order.py: Extensión del modelo de presupuestos de venta
4. product_template.py: Extensión del modelo de productos

ARQUITECTURA DE DATOS:
- Capítulo (1) → Secciones (N) → Productos (N)
- Sale Order (1) → Sale Order Lines (N) con estructura de capítulos
- Integración nativa con modelos estándar de Odoo

FUNCIONALIDADES:
- Gestión de capítulos técnicos estructurados
- Widget JavaScript interactivo para presupuestos
- Cálculo automático de totales por capítulo/sección
- Condiciones particulares editables
- Validaciones de integridad de datos

REFERENCIAS:
- Cada modelo extiende funcionalidades de Odoo estándar
- Comunicación con controllers/main.py para endpoints web
- Integración con wizard/capitulo_wizard.py para gestión
"""

# IMPORTACIÓN DE MODELOS DE DATOS
# Orden de importación respeta dependencias entre modelos

# 1. MODELO BASE: Capítulos técnicos
# Define la estructura principal de capítulos
from . import capitulo

# 2. MODELO RELACIONADO: Secciones de capítulos
# Define las secciones dentro de cada capítulo
from . import capitulo_seccion

# 3. EXTENSIÓN: Presupuestos de venta
# Extiende sale.order con funcionalidad de capítulos
from . import sale_order

# 4. EXTENSIÓN: Plantillas de productos
# Extiende product.template con campos adicionales
from . import product_template
