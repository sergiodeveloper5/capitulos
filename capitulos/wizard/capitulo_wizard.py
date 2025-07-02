from odoo import models, fields, api
from odoo.exceptions import UserError

class CapituloWizardLine(models.TransientModel):
    _name = 'capitulo.wizard.line'
    _description = 'Línea de Configurador de capítulo'

    wizard_id = fields.Many2one('capitulo.wizard', ondelete='cascade')
    componente_id = fields.Many2one('capitulo.componente', required=True)
    cantidad = fields.Float(default=1, required=True)
    precio_unitario = fields.Float(related='componente_id.precio_unitario', readonly=False)

class CapituloWizard(models.TransientModel):
    _name = 'capitulo.wizard'
    _description = 'Configurador de capítulo'

    capitulo_id = fields.Many2one('capitulo.contrato', required=True, string='Capítulo')
    order_id = fields.Many2one('sale.order', string='Pedido de Venta', required=True)
    line_ids = fields.One2many('capitulo.wizard.line', 'wizard_id', string='Componentes')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # Obtener el pedido desde el contexto
        order_id = self.env.context.get('default_order_id') or self.env.context.get('active_id')
        if order_id and 'order_id' in fields:
            res['order_id'] = order_id
        return res

    @api.onchange('capitulo_id')
    def _onchange_capitulo(self):
        if self.capitulo_id:
            lines = []
            for componente in self.capitulo_id.componente_ids:
                if componente.incluir_por_defecto:
                    lines.append((0, 0, {
                        'componente_id': componente.id,
                        'cantidad': componente.cantidad,
                        'precio_unitario': componente.precio_unitario,
                    }))
            self.line_ids = lines
        else:
            self.line_ids = [(5, 0, 0)]

    def add_to_order(self):
        if not self.order_id:
            raise UserError("No se encontró el pedido de venta")

        if not self.line_ids:
            raise UserError("Debe seleccionar al menos un componente")

        order = self.order_id

        # Crear líneas de pedido
        for line in self.line_ids:
            vals = {
                'order_id': order.id,
                'name': f"[{self.capitulo_id.codigo}] {line.componente_id.name}",
                'price_unit': line.precio_unitario,
                'product_uom_qty': line.cantidad,
                'product_uom': line.componente_id.uom_id.id,
            }
            if line.componente_id.product_id:
                vals['product_id'] = line.componente_id.product_id.id
            
            order.order_line.create(vals)

        # Añadir capítulo a la lista de capítulos aplicados
        order.capitulo_ids = [(4, self.capitulo_id.id)]

        # Añadir condiciones legales si existen
        if self.capitulo_id.condiciones_legales:
            nota_capitulo = f"\n\nCondiciones del capítulo {self.capitulo_id.codigo}:\n{self.capitulo_id.condiciones_legales}"
            order.note = (order.note or '') + nota_capitulo

        return {'type': 'ir.actions.act_window_close'}