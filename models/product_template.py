"""
EXTENSIÓN DEL MODELO DE PRODUCTOS
=================================

Este archivo extiende el modelo product.template de Odoo para añadir
funcionalidades específicas del sistema de capítulos técnicos.

FUNCIONALIDADES AÑADIDAS:
- Clasificación de productos por capítulo
- Categorización por tipo de sección (alquiler, montaje, etc.)
- Métodos de búsqueda especializados para filtrado

CAMPOS AÑADIDOS:
- capitulo_id: Relación con el capítulo al que pertenece el producto
- tipo_seccion: Clasificación del producto por tipo de servicio

MÉTODOS AÑADIDOS:
- _search_by_capitulo_seccion: Búsqueda filtrada por capítulo y tipo

@author: Sistema de Capítulos Técnicos
@version: 1.0
@since: 2024
"""

from odoo import models, fields, api

class ProductTemplate(models.Model):
    """
    EXTENSIÓN DE PLANTILLA DE PRODUCTO
    =================================
    
    Extiende el modelo estándar de productos para integrar la funcionalidad
    de capítulos técnicos, permitiendo clasificar productos por capítulo
    y tipo de sección para facilitar su organización en presupuestos.
    """
    _inherit = 'product.template'
    
    # ==========================================
    # CAMPOS DE CLASIFICACIÓN
    # ==========================================
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato',
        string='Capítulo',
        help='Capítulo técnico al que pertenece este producto por defecto'
    )
    
    tipo_seccion = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('desmontaje', 'Desmontaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros')
    ], 
    string='Tipo de Sección',
    help='Clasificación del producto según el tipo de servicio que representa'
    )

    # ==========================================
    # MÉTODOS DE BÚSQUEDA ESPECIALIZADOS
    # ==========================================
    
    @api.model
    def _search_by_capitulo_seccion(self, capitulo_id=None, tipo_seccion=None):
        """
        BÚSQUEDA FILTRADA POR CAPÍTULO Y SECCIÓN
        =======================================
        
        Método especializado para buscar productos filtrados por:
        - Capítulo específico
        - Tipo de sección específico
        - Combinación de ambos criterios
        
        Args:
            capitulo_id (int, optional): ID del capítulo para filtrar
            tipo_seccion (str, optional): Tipo de sección para filtrar
            
        Returns:
            recordset: Productos que coinciden con los criterios
            
        Ejemplo de uso:
            # Buscar productos de alquiler del capítulo 5
            productos = self.env['product.template']._search_by_capitulo_seccion(
                capitulo_id=5, 
                tipo_seccion='alquiler'
            )
        """
        domain = []
        
        # Filtrar por capítulo si se especifica
        if capitulo_id:
            domain.append(('capitulo_id', '=', capitulo_id))
            
        # Filtrar por tipo de sección si se especifica
        if tipo_seccion:
            domain.append(('tipo_seccion', '=', tipo_seccion))
            
        return self.search(domain)