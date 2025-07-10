# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Capitulo(models.Model):
    _name = 'capitulo.capitulo'
    _description = 'Capítulo de Andamios'
    _order = 'sequence, name'

    name = fields.Char('Nombre del Capítulo', required=True)
    description = fields.Text('Descripción')
    sequence = fields.Integer('Secuencia', default=10)
    sale_order_id = fields.Many2one('sale.order', 'Presupuesto', ondelete='cascade')
    
    # Secciones del capítulo
    seccion_ids = fields.One2many('capitulo.seccion', 'capitulo_id', 'Secciones')
    
    # Total del capítulo
    total_capitulo = fields.Monetary('Total del Capítulo', compute='_compute_total_capitulo', store=True)
    currency_id = fields.Many2one('res.currency', related='sale_order_id.currency_id', store=True)
    
    # Condiciones particulares
    condiciones_particulares = fields.Html('Condiciones Particulares')
    
    # Control de plantillas
    es_plantilla = fields.Boolean('Guardar como Plantilla', default=False)
    plantilla_origen_id = fields.Many2one('capitulo.plantilla', 'Plantilla Origen')
    
    # Estado
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
    ], default='draft', string='Estado')
    
    @api.depends('seccion_ids.total_seccion')
    def _compute_total_capitulo(self):
        """Calcular el total del capítulo sumando todas las secciones"""
        for record in self:
            record.total_capitulo = sum(record.seccion_ids.mapped('total_seccion'))
    
    @api.model
    def create_from_template(self, template_id, sale_order_id):
        """Crear capítulo desde plantilla"""
        template = self.env['capitulo.plantilla'].browse(template_id)
        
        # Crear el capítulo
        capitulo_vals = {
            'name': template.name,
            'description': template.description,
            'sale_order_id': sale_order_id,
            'condiciones_particulares': template.condiciones_particulares,
            'plantilla_origen_id': template.id,
        }
        capitulo = self.create(capitulo_vals)
        
        # Crear las secciones desde la plantilla
        for template_seccion in template.seccion_ids:
            seccion_vals = {
                'name': template_seccion.name,
                'capitulo_id': capitulo.id,
                'sequence': template_seccion.sequence,
                'es_fija': template_seccion.es_fija,
            }
            seccion = self.env['capitulo.seccion'].create(seccion_vals)
            
            # Crear los productos de la sección
            for template_producto in template_seccion.producto_ids:
                producto_vals = {
                    'product_id': template_producto.product_id.id,
                    'seccion_id': seccion.id,
                    'quantity': template_producto.quantity,
                    'price_unit': template_producto.price_unit,
                    'sequence': template_producto.sequence,
                    'es_fijo': template_producto.es_fijo,
                }
                self.env['capitulo.producto'].create(producto_vals)
        
        return capitulo
    
    def save_as_template(self):
        """Guardar capítulo como plantilla"""
        template_vals = {
            'name': self.name,
            'description': self.description,
            'condiciones_particulares': self.condiciones_particulares,
        }
        template = self.env['capitulo.plantilla'].create(template_vals)
        
        # Copiar secciones a la plantilla
        for seccion in self.seccion_ids:
            seccion_template_vals = {
                'name': seccion.name,
                'plantilla_id': template.id,
                'sequence': seccion.sequence,
                'es_fija': seccion.es_fija,
            }
            seccion_template = self.env['capitulo.seccion.plantilla'].create(seccion_template_vals)
            
            # Copiar productos de la sección
            for producto in seccion.producto_ids:
                producto_template_vals = {
                    'product_id': producto.product_id.id,
                    'seccion_plantilla_id': seccion_template.id,
                    'quantity': producto.quantity,
                    'price_unit': producto.price_unit,
                    'sequence': producto.sequence,
                    'es_fijo': producto.es_fijo,
                }
                self.env['capitulo.producto.plantilla'].create(producto_template_vals)
        
        return template