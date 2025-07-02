from odoo import models, fields

class CapituloComponente(models.Model):
    _name = 'capitulo.componente'
    _description = 'Componente del Capítulo'
    _rec_name = 'name'

    capitulo_id = fields.Many2one('capitulo.contrato', string='Capítulo', required=True, ondelete='cascade')
    name = fields.Char(string="Nombre", required=True)
    type = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('seguro', 'Seguro'),
        ('montaje', 'Montaje'),
        ('desmontaje', 'Desmontaje'),
        ('transporte', 'Transporte'),
        ('otros', 'Otros'),
    ], string='Tipo', default='otros', required=True)
    precio_unitario = fields.Float(string="Precio Unitario", required=True)
    cantidad = fields.Float(string="Cantidad", default=1, required=True)
    uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit'))
    incluir_por_defecto = fields.Boolean(string="Incluir por Defecto", default=True)
    product_id = fields.Many2one('product.product', string='Producto')