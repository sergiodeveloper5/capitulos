# -*- coding: utf-8 -*-

"""
MANIFIESTO DEL MÓDULO DE CAPÍTULOS TÉCNICOS
==========================================

Este archivo define la configuración principal del módulo de capítulos técnicos
para Odoo, incluyendo metadatos, dependencias, archivos de datos y recursos.

INFORMACIÓN DEL MÓDULO:
- Nombre: Gestión de Capítulos Contratados
- Versión: 18.0.1.1.0 (Compatible con Odoo 18.0)
- Categoría: Sales (Ventas)
- Licencia: LGPL-3

FUNCIONALIDADES PRINCIPALES:
- Gestión de capítulos técnicos estructurados
- Sistema de plantillas reutilizables
- Wizard intuitivo para gestión de capítulos
- Integración completa con pedidos de venta
- Widget de acordeón para visualización avanzada

DEPENDENCIAS:
- base: Funcionalidades básicas de Odoo
- sale_management: Gestión de ventas
- product: Gestión de productos
- uom: Unidades de medida

ARCHIVOS INCLUIDOS:
- Vistas XML para todos los modelos
- Archivos de seguridad y permisos
- Recursos web (CSS, JavaScript, Templates)
- Configuraciones de menús y acciones

@author: Sergio Vadillo
@version: 18.0.1.1.0
@since: 2024
@license: LGPL-3
@website: https://github.com/sergiodeveloper5/capitulos.git
"""

{
    # ==========================================
    # INFORMACIÓN BÁSICA DEL MÓDULO
    # ==========================================
    
    'name': 'Gestión de Capítulos Contratados',
    'version': '18.0.1.1.0',
    'category': 'Sales',
    'summary': 'Gestión de capítulos técnicos y contratación de servicios agrupados',
    'description': """
        MÓDULO DE CAPÍTULOS TÉCNICOS PARA ODOO
        =====================================
        
        Gestión avanzada de capítulos técnicos como servicios completos con productos 
        configurables para presupuestos de venta estructurados.
        
        CARACTERÍSTICAS PRINCIPALES:
        • Organización jerárquica de presupuestos en capítulos y secciones
        • Sistema de plantillas reutilizables para estandarización
        • Wizard intuitivo para gestión y creación de capítulos
        • Widget de acordeón para visualización avanzada
        • Integración completa con el módulo de ventas de Odoo
        • Gestión de dependencias entre plantillas y capítulos
        • Secciones especializadas por tipo de servicio
        • Productos opcionales y configurables
        • Cálculo automático de totales y subtotales
        
        CASOS DE USO:
        • Empresas de servicios técnicos
        • Proyectos con múltiples fases
        • Presupuestos complejos estructurados
        • Servicios de alquiler, montaje y desmontaje
        • Gestión de plantillas estándar
    """,
    
    # ==========================================
    # METADATOS DEL DESARROLLADOR
    # ==========================================
    
    'author': 'Sergio Vadillo',
    'website': 'https://github.com/sergiodeveloper5/capitulos.git',
    'license': 'LGPL-3',
    
    # ==========================================
    # DEPENDENCIAS DEL MÓDULO
    # ==========================================
    
    'depends': [
        'base',              # Funcionalidades básicas de Odoo
        'sale_management',   # Gestión de ventas y presupuestos
        'product',          # Gestión de productos
        'uom',              # Unidades de medida
    ],
    
    # ==========================================
    # ARCHIVOS DE DATOS Y VISTAS
    # ==========================================
    
    'data': [
        # Seguridad y permisos
        'security/ir.model.access.csv',
        
        # Vistas principales
        'views/capitulo_views.xml',           # Vistas de capítulos y plantillas
        'views/sale_order_views.xml',         # Extensión de vistas de pedidos
        'views/capitulo_wizard_view.xml',     # Vista del wizard de gestión
        'views/product_views.xml',            # Extensión de vistas de productos
    ],
    
    # ==========================================
    # RECURSOS WEB (CSS, JS, TEMPLATES)
    # ==========================================
    
    'assets': {
        'web.assets_backend': [
            # Estilos CSS para el widget de acordeón
            'capitulos/static/src/css/capitulos_accordion.css',
            
            # JavaScript del widget de acordeón
            'capitulos/static/src/js/capitulos_accordion_widget.js',
            
            # Templates XML para el frontend
            'capitulos/static/src/xml/capitulos_accordion_templates.xml',
        ],
    },
    
    # ==========================================
    # CONFIGURACIÓN DE INSTALACIÓN
    # ==========================================
    
    'installable': True,        # El módulo puede ser instalado
    'auto_install': False,      # No se instala automáticamente
    'application': True,        # Es una aplicación independiente
}