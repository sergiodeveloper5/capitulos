{
    'name': 'Capítulos Contratados',
    'version': '1.0.0',
    'summary': 'Gestión de capítulos técnicos y contratación de servicios agrupados',
    'description': '''
Permite gestionar capítulos como servicios técnicos completos que incluyen varios componentes (alquiler, montaje, seguros, etc.).
Incluye wizard para añadir capítulos a presupuestos, cálculo de precios y condiciones legales.
''',
    'author': 'Sergio Vadillo',
    'website': 'https://github.com/sergiodeveloper5/capitulos.git',
    'license': 'LGPL-3',
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/capitulo_views.xml',
        'views/sale_order_views.xml',
        'views/capitulo_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
}
