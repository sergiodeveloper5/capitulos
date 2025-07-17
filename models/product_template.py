# -*- coding: utf-8 -*-
"""
Extensión del Modelo Product Template para Capítulos Técnicos
=============================================================

Este módulo extiende el modelo product.template de Odoo para añadir funcionalidad
específica relacionada con capítulos técnicos. Permite categorizar productos
por capítulos y tipos de sección para facilitar su organización y búsqueda.

Funcionalidades añadidas:
- Relación con capítulos técnicos
- Categorización por tipo de sección
- Métodos de búsqueda especializados
- Filtrado avanzado de productos

Autor: Sergio
Fecha: 2024
Versión: 1.0
"""

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """
    Extensión del modelo product.template para soporte de capítulos técnicos.
    
    Esta extensión añade campos y métodos específicos para la gestión de productos
    dentro del contexto de capítulos técnicos, permitiendo una mejor organización
    y categorización de los productos según su uso en diferentes tipos de secciones.
    
    Características añadidas:
    - Relación directa con capítulos técnicos
    - Categorización por tipo de sección (alquiler, montaje, etc.)
    - Métodos de búsqueda especializados
    - Filtrado avanzado para selección de productos
    """
    _inherit = 'product.template'
    
    # ========================================
    # CAMPOS DE RELACIÓN CON CAPÍTULOS
    # ========================================
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato',
        string='Capítulo',
        help='Capítulo técnico al que pertenece este producto por defecto. '
             'Permite organizar productos por capítulos específicos.'
    )
    
    # ========================================
    # CAMPOS DE CATEGORIZACIÓN
    # ========================================
    
    tipo_seccion = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('desmontaje', 'Desmontaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros')
    ], string='Tipo de Sección',
       help='Tipo de sección donde se utiliza habitualmente este producto. '
            'Facilita la categorización y búsqueda de productos por uso.')
    
    # ========================================
    # MÉTODOS DE BÚSQUEDA ESPECIALIZADOS
    # ========================================
    
    @api.model
    def _search_by_capitulo_seccion(self, capitulo_id=None, tipo_seccion=None):
        """
        Método de búsqueda especializado para productos por capítulo y sección.
        
        Este método permite buscar productos filtrados por capítulo y/o tipo de
        sección, facilitando la selección de productos relevantes en contextos
        específicos del módulo de capítulos técnicos.
        
        Args:
            capitulo_id (int, optional): ID del capítulo para filtrar productos.
                Si se proporciona, solo se devolverán productos asociados a este capítulo.
            tipo_seccion (str, optional): Tipo de sección para filtrar productos.
                Debe ser uno de los valores válidos del campo tipo_seccion.
                
        Returns:
            product.template: Recordset de productos que coinciden con los criterios
            
        Examples:
            # Buscar productos de alquiler
            productos_alquiler = self._search_by_capitulo_seccion(tipo_seccion='alquiler')
            
            # Buscar productos de un capítulo específico
            productos_capitulo = self._search_by_capitulo_seccion(capitulo_id=1)
            
            # Buscar productos de montaje de un capítulo específico
            productos_montaje = self._search_by_capitulo_seccion(
                capitulo_id=1, 
                tipo_seccion='montaje'
            )
        """
        # Construir dominio de búsqueda dinámicamente
        domain = []
        
        if capitulo_id:
            domain.append(('capitulo_id', '=', capitulo_id))
            
        if tipo_seccion:
            domain.append(('tipo_seccion', '=', tipo_seccion))
            
        return self.search(domain)