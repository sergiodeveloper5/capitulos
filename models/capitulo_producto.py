# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloProducto(models.Model):
    _name = 'capitulo.producto'
    _description = 'Producto de Capítulo'
    _order = 'sequence, id'

    seccion_id = fields.Many2one('capitulo.seccion', 'Sección', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    
    # Campos de cantidad y precio
    quantity = fields.Float('Cantidad', default=1.0, digits='Product Unit of Measure')
    price_unit = fields.Float('Precio Unitario', digits='Product Price')
    subtotal = fields.Monetary('Subtotal', compute='_compute_subtotal', store=True)
    
    # Campos relacionados del producto
    product_name = fields.Char(related='product_id.name', string='Nombre del Producto')
    product_uom_id = fields.Many2one(related='product_id.uom_id', string='Unidad de Medida')
    
    # Control y orden
    sequence = fields.Integer('Secuencia', default=10)
    currency_id = fields.Many2one('res.currency', related='seccion_id.capitulo_id.sale_order_id.currency_id')
    
    # Control de permisos
    es_fijo = fields.Boolean('Producto Fijo', default=False,
                            help="Si está marcado, los comerciales no podrán eliminar este producto")
    
    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for producto in self:
            producto.subtotal = producto.quantity * producto.price_unit
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            # Establecer precio por defecto del producto
            self.price_unit = self.product_id.list_price
    
    def add_to_sale_order_lines(self):
        """Agregar este producto como línea de venta al presupuesto"""
        sale_order = self.seccion_id.capitulo_id.sale_order_id
        if sale_order:
            line_vals = {
                'order_id': sale_order.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'price_unit': self.price_unit,
                'name': f"[{self.seccion_id.capitulo_id.name}] {self.seccion_id.name} - {self.product_id.name}",
            }
            self.env['sale.order.line'].create(line_vals)

class CapituloProductoPlantilla(models.Model):
    _name = 'capitulo.producto.plantilla'
    _description = 'Producto de Plantilla de Capítulo'
    _order = 'sequence, id'

    seccion_plantilla_id = fields.Many2one('capitulo.seccion.plantilla', 'Sección Plantilla', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    
    # Campos de cantidad y precio
    quantity = fields.Float('Cantidad', default=1.0, digits='Product Unit of Measure')
    price_unit = fields.Float('Precio Unitario', digits='Product Price')
    
    # Campos relacionados del producto
    product_name = fields.Char(related='product_id.name', string='Nombre del Producto')
    product_uom_id = fields.Many2one(related='product_id.uom_id', string='Unidad de Medida')
    
    # Control y orden
    sequence = fields.Integer('Secuencia', default=10)
    
    # Control de permisos
    es_fijo = fields.Boolean('Producto Fijo', default=False)