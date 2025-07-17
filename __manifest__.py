# -*- coding: utf-8 -*-
"""
ARCHIVO DE MANIFIESTO DEL MÓDULO CAPÍTULOS CONTRATADOS
=====================================================

Este archivo define la configuración principal del módulo de Odoo para la gestión
de capítulos técnicos en presupuestos de venta.

FUNCIONALIDAD PRINCIPAL:
- Gestión de capítulos técnicos como servicios agrupados
- Widget JavaScript interactivo con acordeón para visualización
- Wizard para creación y configuración de capítulos
- Integración completa con el módulo de ventas de Odoo

ARQUITECTURA:
- Backend: Python (modelos ORM, lógica de negocio)
- Frontend: JavaScript OWL (widget interactivo)
- Vistas: XML QWeb (templates y formularios)
- Estilos: CSS (diseño responsive y moderno)

DEPENDENCIAS:
- base: Funcionalidades básicas de Odoo
- sale_management: Gestión de ventas y presupuestos
- product: Gestión de productos
- uom: Unidades de medida

AUTOR: Sergio Vadillo
VERSIÓN: 18.0.1.0.0 (Compatible con Odoo 18.0)
LICENCIA: LGPL-3
"""

{
    # INFORMACIÓN BÁSICA DEL MÓDULO
    'name': 'Gestión de Capítulos Contratados',
    'version': '18.0.1.0.0',  # Formato: [versión_odoo].[major].[minor].[patch]
    'category': 'Sales',       # Categoría en el App Store de Odoo
    'summary': 'Gestión de capítulos técnicos y contratación de servicios agrupados',
    
    # DESCRIPCIÓN DETALLADA
    'description': """
    Gestión de Capítulos Técnicos para Presupuestos de Venta
    ========================================================
    
    Este módulo permite organizar presupuestos de venta en capítulos técnicos
    estructurados, facilitando la gestión de servicios complejos agrupados.
    
    Características principales:
    • Widget interactivo con acordeón para visualización de capítulos
    • Creación de capítulos con secciones y productos configurables
    • Wizard intuitivo para gestión de capítulos y secciones
    • Condiciones particulares editables por sección
    • Cálculo automático de totales por capítulo y sección
    • Integración nativa con el flujo de ventas de Odoo
    • Diseño responsive y moderno
    
    Casos de uso:
    • Presupuestos de servicios técnicos complejos
    • Proyectos con múltiples fases o capítulos
    • Servicios agrupados por especialidad
    • Contratos con condiciones particulares por sección
    """,
    
    # METADATOS DEL DESARROLLADOR
    'author': 'Sergio Vadillo',
    'website': 'https://github.com/sergiodeveloper5/capitulos.git',
    
    # DEPENDENCIAS DEL MÓDULO
    # Estos módulos deben estar instalados antes que este
    'depends': [
        'base',              # Funcionalidades básicas de Odoo (ORM, usuarios, etc.)
        'sale_management',   # Gestión de ventas y presupuestos
        'product',          # Gestión de productos y variantes
        'uom',              # Unidades de medida
    ],
    
    # ARCHIVOS DE DATOS Y VISTAS
    # Se cargan en orden durante la instalación
    'data': [
        # 1. SEGURIDAD: Permisos de acceso a modelos
        'security/ir.model.access.csv',
        
        # 2. VISTAS: Formularios y listas (orden de dependencias)
        'views/capitulo_views.xml',        # Vistas de capítulos base
        'views/sale_order_views.xml',      # Extensión de vistas de venta
        'views/capitulo_wizard_view.xml',  # Wizard de gestión
        'views/product_views.xml',         # Extensión de vistas de producto
    ],
    
    # RECURSOS FRONTEND (JavaScript, CSS, XML)
    # Se cargan en el navegador para funcionalidad frontend
    'assets': {
        'web.assets_backend': [
            # ESTILOS CSS: Diseño visual del widget
            'capitulos/static/src/css/capitulos_accordion.css',
            
            # JAVASCRIPT: Lógica del widget interactivo
            'capitulos/static/src/js/capitulos_accordion_widget.js',
            
            # TEMPLATES XML: Estructura HTML del widget
            'capitulos/static/src/xml/capitulos_accordion_templates.xml',
        ],
    },
    
    # CONFIGURACIÓN DE INSTALACIÓN
    'installable': True,     # El módulo puede ser instalado
    'auto_install': False,   # No se instala automáticamente
    'application': True,     # Es una aplicación principal (aparece en Apps)
    'license': 'LGPL-3',    # Licencia de código abierto
}