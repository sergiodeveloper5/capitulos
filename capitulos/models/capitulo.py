from odoo import models, fields

class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo Contratado'

    name = fields.Char(required=True)
    codigo = fields.Char(required=True)
    descripcion = fields.Text()
    condiciones_legales = fields.Html(string="Condiciones Legales")
    componente_ids = fields.One2many('capitulo.componente', 'capitulo_id',
    string='Componentes')
