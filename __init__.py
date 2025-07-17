# -*- coding: utf-8 -*-
"""
==========================================
INICIALIZADOR DEL MÓDULO CAPÍTULOS TÉCNICOS
==========================================

@file __init__.py
@description Archivo de inicialización principal del módulo
@author Sergio Vadillo
@version 18.0.1.1.0
@since 2024

@overview
Este archivo se ejecuta cuando se importa el módulo y es responsable
de importar todos los submódulos necesarios para el funcionamiento
del sistema de capítulos técnicos.

@imports
- models: Importa todos los modelos de datos
- controllers: Importa los controladores web
- wizard: Importa los asistentes/wizards

@note
El orden de importación es importante para evitar dependencias circulares
y asegurar que todos los componentes se carguen correctamente.
"""

# Importación de submódulos principales
from . import models      # Modelos de datos (capitulo, sale_order, etc.)
from . import controllers # Controladores web para endpoints HTTP
from . import wizard      # Asistentes para funcionalidades específicas
