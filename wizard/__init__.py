# -*- coding: utf-8 -*-
"""
INICIALIZACIÓN DEL PAQUETE WIZARD
=================================

Este archivo inicializa los wizards (asistentes) del módulo.
Los wizards proporcionan interfaces de usuario para operaciones
complejas que requieren múltiples pasos o validaciones.

WIZARDS INCLUIDOS:
- capitulo_wizard.py: Asistente para gestión de capítulos
  * Creación de capítulos desde plantillas
  * Configuración de secciones y productos
  * Validación de datos antes de guardar
  * Interfaz simplificada para usuarios

FUNCIONALIDAD:
- Interfaces de usuario paso a paso
- Validación de datos en tiempo real
- Configuración guiada de capítulos complejos
- Integración con modelos de datos principales

REFERENCIAS:
- models/capitulo.py: Modelo principal de capítulos
- models/capitulo_seccion.py: Modelo de secciones
- views/capitulo_wizard_views.xml: Vistas del wizard
"""

# IMPORTACIÓN DEL WIZARD PRINCIPAL
# Asistente para gestión completa de capítulos
from . import capitulo_wizard