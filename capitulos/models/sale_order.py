from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    capitulo_ids = fields.Many2many('capitulo.contrato', string='Capítulos Aplicados')
    
    def action_add_capitulo(self):
        """Acción para abrir el wizard de capítulos"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Añadir Capítulo',
            'res_model': 'capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }