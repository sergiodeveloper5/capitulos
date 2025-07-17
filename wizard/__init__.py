# -*- coding: utf-8 -*-
"""
==========================================
INICIALIZADOR DE ASISTENTES (WIZARDS)
==========================================

@file wizard/__init__.py
@description Inicializador del paquete de asistentes/wizards
@author Sergio Vadillo
@version 18.0.1.1.0
@since 2024

@overview
Este archivo importa todos los asistentes (wizards) del módulo de capítulos
técnicos. Los wizards son ventanas modales que guían al usuario a través
de procesos específicos de manera paso a paso.

@wizards
- import_capitulos: Asistente para importación masiva de capítulos
- export_capitulos: Asistente para exportación de datos de capítulos
- duplicate_capitulos: Asistente para duplicación de estructuras
- Otros asistentes específicos según necesidades

@functionality
Los wizards proporcionan interfaces intuitivas para:
- Importación/exportación de datos
- Procesos de configuración complejos
- Operaciones masivas sobre capítulos
- Validación y transformación de datos

@note
Los wizards se registran automáticamente como modelos transitorios
cuando se importa este paquete.
"""

# Importación de todos los asistentes del módulo
# from . import import_capitulos    # Asistente de importación (si existe)
# from . import export_capitulos    # Asistente de exportación (si existe)

# Nota: Actualmente no hay wizards implementados, pero esta estructura
# está preparada para futuras extensiones del módulo

from . import capitulo_wizard