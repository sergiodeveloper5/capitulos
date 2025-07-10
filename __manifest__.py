# -*- coding: utf-8 -*-
{
    'name': 'Sermaco - Gestión de Capítulos y Secciones',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Módulo para gestionar plantillas de capítulos con secciones predefinidas para presupuestos de Sermaco',
    'description': """
        Sistema de Capítulos y Secciones para Sermaco
        =============================================
        
        Este módulo permite:
        * Crear plantillas de capítulos con secciones predefinidas
        * Control de permisos por roles (Administrador/Técnico vs Comercial)
        * Secciones fijas no eliminables para comerciales
        * Restricciones específicas por tipo de sección
        * Integración completa con presupuestos de venta
        
        Empresa: Sermaco (Andamios y Equipos de Construcción)
    """,
    'author': 'Sermaco',
    'website': 'https://www.sermaco.com',
    'depends': ['base', 'sale'],
    'data': [
        # Seguridad
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Datos
        'data/sale_order_chapter_template_data.xml',
        'data/conditions_section_data.xml',
        
        # Vistas
        'views/sale_order_chapter_template_views.xml',
        'views/sale_order_chapter_section_template_views.xml',
        'views/sale_order_views.xml',
        'wizards/sale_order_chapter_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}