# -*- coding: utf-8 -*-
{
    # INFORMACIÓN BÁSICA DEL MÓDULO
    'name': 'Gestión de Capítulos Contratados',
    'version': '18.0.1.0.0',
    'category': 'Sales',
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
    'depends': [
        'base',
        'sale_management',
        'product',
        'uom',
    ],
    
    # ARCHIVOS DE DATOS Y VISTAS
    'data': [
        'security/ir.model.access.csv',
        'views/capitulo_views.xml',
        'views/sale_order_views.xml',
        'views/capitulo_wizard_view.xml',
        'views/product_views.xml',
    ],
    
    # RECURSOS FRONTEND
    'assets': {
        'web.assets_backend': [
            'capitulos/static/src/css/capitulos_accordion.css',
            'capitulos/static/src/js/capitulos_accordion_widget.js',
            'capitulos/static/src/xml/capitulos_accordion_templates.xml',
        ],
    },
    
    # CONFIGURACIÓN DE INSTALACIÓN
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}