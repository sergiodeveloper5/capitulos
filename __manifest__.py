# -*- coding: utf-8 -*-
{
    'name': 'Capítulos de Andamios - Sermaco',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestión de capítulos de andamios para presupuestos',
    'description': '''
        Módulo para gestionar capítulos de andamios en presupuestos de venta.
        Permite crear capítulos con secciones y productos, guardar como plantillas
        y gestionar permisos diferenciados para admin y comerciales.
    ''',
    'author': 'Sermaco',
    'website': '',
    'depends': ['sale_management', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_order_views.xml',
        'wizard/capitulo_wizard_views.xml',
        'data/capitulo_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}