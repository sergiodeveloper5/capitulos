# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloSeccion(models.Model):
    _name = 'capitulo.seccion'
    _description = 'Sección de Capítulo'
    _order = 'sequence, name'

    name = fields.Char('Nombre de la Sección', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    capitulo_id = fields.Many2one('capitulo.capitulo', 'Capítulo', required=True, ondelete='cascade')
    
    # Productos de la sección
    producto_ids = fields.One2many('capitulo.producto', 'seccion_id', 'Productos')
    
    # Control de permisos
    es_fija = fields.Boolean('Sección Fija', default=False, 
                            help="Si está marcado, los comerciales no podrán eliminar esta sección")
    
    # Campos calculados
    total_seccion = fields.Monetary('Total Sección', compute='_compute_total_seccion', store=True)
    currency_id = fields.Many2one('res.currency', related='capitulo_id.sale_order_id.currency_id')
    
    @api.depends('producto_ids.subtotal')
    def _compute_total_seccion(self):
        for seccion in self:
            seccion.total_seccion = sum(producto.subtotal for producto in seccion.producto_ids)
    
    @api.model
    def create_default_sections(self, capitulo_id):
        """Crear secciones por defecto: Alquiler y Montaje"""
        default_sections = [
            {'name': 'Alquiler', 'sequence': 10, 'es_fija': True},
            {'name': 'Montaje', 'sequence': 20, 'es_fija': True},
        ]
        
        for section_data in default_sections:
            section_data['capitulo_id'] = capitulo_id
            self.create(section_data)

class CapituloSeccionPlantilla(models.Model):
    _name = 'capitulo.seccion.plantilla'
    _description = 'Sección de Plantilla de Capítulo'
    _order = 'sequence, name'

    name = fields.Char('Nombre de la Sección', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    plantilla_id = fields.Many2one('capitulo.plantilla', 'Plantilla', required=True, ondelete='cascade')
    
    # Productos de la sección plantilla
    producto_ids = fields.One2many('capitulo.producto.plantilla', 'seccion_plantilla_id', 'Productos')
    
    # Control de permisos
    es_fija = fields.Boolean('Sección Fija', default=False)