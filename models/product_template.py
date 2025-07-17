from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato',
        string='Capítulo',
        help='Capítulo al que pertenece este producto'
    )
    
    tipo_seccion = fields.Selection([
        ('alquiler', 'Alquiler'),
        ('montaje', 'Montaje'),
        ('desmontaje', 'Desmontaje'),
        ('portes', 'Portes'),
        ('otros', 'Otros')
    ], string='Tipo de Sección')
    
    @api.model
    def _search_by_capitulo_seccion(self, capitulo_id=None, tipo_seccion=None):
        domain = []
        if capitulo_id:
            domain.append(('capitulo_id', '=', capitulo_id))
        if tipo_seccion:
            domain.append(('tipo_seccion', '=', tipo_seccion))
        return self.search(domain)