{
    'name': 'Gestión de Capítulos Contratados',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestión de capítulos técnicos y contratación de servicios agrupados',
    'description': "Gestión de capítulos técnicos como servicios completos con productos configurables para presupuestos de venta.",
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
        'views/product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'capitulos/static/src/css/capitulos_accordion.css',
            'capitulos/static/src/js/capitulos_accordion_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}