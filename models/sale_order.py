from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    capitulo_ids = fields.Many2many(
        'capitulo.contrato', 
        string='Capítulos Aplicados',
        help="Capítulos técnicos aplicados a este pedido de venta"
    )
    
    def action_add_capitulo(self):
        """Acción para abrir el wizard de capítulos"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestionar Capítulos del Presupuesto',
            'res_model': 'capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'active_id': self.id,
                'active_model': 'sale.order'
            }
        }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    es_encabezado_capitulo = fields.Boolean(
        string='Es Encabezado de Capítulo',
        default=False,
        help="Indica si esta línea es un encabezado de capítulo (no modificable)"
    )
    
    es_encabezado_seccion = fields.Boolean(
        string='Es Encabezado de Sección',
        default=False,
        help="Indica si esta línea es un encabezado de sección (no modificable)"
    )
    
    def unlink(self):
        """Previene la eliminación de encabezados de capítulos y secciones"""
        for line in self:
            if line.es_encabezado_capitulo:
                raise UserError(
                    f"No se puede eliminar el encabezado del capítulo: {line.name}\n"
                    "Los encabezados de capítulos son elementos estructurales del presupuesto."
                )
            if line.es_encabezado_seccion:
                raise UserError(
                    f"No se puede eliminar el encabezado de la sección: {line.name}\n"
                    "Los encabezados de secciones son elementos estructurales del presupuesto."
                )
        return super().unlink()
    
    def write(self, vals):
        """Previene la modificación de campos críticos en encabezados"""
        protected_fields = ['name', 'product_id', 'product_uom_qty', 'price_unit', 'sequence']
        
        for line in self:
            if (line.es_encabezado_capitulo or line.es_encabezado_seccion):
                # Verificar si se está intentando modificar campos protegidos
                for field in protected_fields:
                    if field in vals:
                        tipo = "capítulo" if line.es_encabezado_capitulo else "sección"
                        raise UserError(
                            f"No se puede modificar el encabezado de {tipo}: {line.name}\n"
                            f"Los encabezados son elementos estructurales del presupuesto y no se pueden editar."
                        )
        
        return super().write(vals)