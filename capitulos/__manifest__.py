{
    'name': 'Gestión de Capítulos Contratados',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestión de capítulos técnicos y contratación de servicios agrupados',
    'description': """
Gestión de Capítulos Contratados
===============================

Este módulo permite gestionar capítulos como servicios técnicos completos que incluyen varios componentes.

Características principales:
* Gestión de capítulos técnicos agrupados
* Componentes configurables (alquiler, montaje, seguros, etc.)
* Wizard para añadir capítulos a presupuestos
* Cálculo automático de precios
* Condiciones legales por capítulo
* Integración completa con el módulo de ventas
""",
    'author': 'Sergio Vadillo',
    'website': 'https://github.com/sergiodeveloper5/capitulos.git',
    'depends': [
        'base',
        'sale_management',
        'product',
        'uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/capitulo_views.xml',
        'views/sale_order_views.xml',
        'views/capitulo_wizard_view.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}