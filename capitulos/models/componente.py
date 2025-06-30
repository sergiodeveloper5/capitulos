from odoo import models, fields

class CapituloComponente(models.Model):
    _name = 'capitulo.componente'
    _description = 'Componente del Capítulo'

    capitulo_id = fields.Many2one('capitulo.contrato', required=True, ondelete='cascade')
    nombre = fields.Char(required=True)
    tipo = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('seguro', 'Seguro'),
        ('montaje', 'Montaje'),
        ('desmontaje', 'Desmontaje'),
        ('transporte', 'Transporte'),
        ('otros', 'Otros'),
    ], default='otros')
    precio_unitario = fields.Float(required=True)
    cantidad = fields.Float(default=1)
    uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit'))
    incluir_por_defecto = fields.Boolean(default=True)
    product_id = fields.Many2one('product.product', string='Producto')
