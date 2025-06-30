from odoo import models, fields, api

class CapituloWizardLine(models.TransientModel):
    _name = 'capitulo.wizard.line'
    _description = 'Línea de Configurador de capítulo'

    wizard_id = fields.Many2one('capitulo.wizard')
    componente_id = fields.Many2one('capitulo.componente', required=True)
    cantidad = fields.Float(default=1)
    precio_unitario = fields.Float(related='componente_id.precio_unitario')

class CapituloWizard(models.TransientModel):
    _name = 'capitulo.wizard'
    _description = 'Configurador de capítulo'

    capitulo_id = fields.Many2one('capitulo.contrato', required=True)
    line_ids = fields.One2many('capitulo.wizard.line', 'wizard_id', string='Líneas')
    componente_ids = fields.Many2many('capitulo.componente') # Este campo ya no sería estrictamente necesario si usas line_ids

    @api.onchange('capitulo_id')
    def _onchange_capitulo(self):
        self.line_ids = [(5, 0, 0)] # Limpiar líneas existentes de forma eficiente
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

    def add_to_order(self):
        order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        for line in self.line_ids: # Iterar sobre las líneas del wizard
            vals = {
                'order_id': order.id,
                'name': f"[{self.capitulo_id.codigo}] {line.componente_id.nombre}",
                'price_unit': line.precio_unitario, # Usar el precio de la línea del wizard
                'product_uom_qty': line.cantidad,   # Usar la cantidad de la línea del wizard
                'product_uom': line.componente_id.uom_id.id, # Asegúrate de usar la UoM del componente
            }
            if line.componente_id.product_id:
                vals['product_id'] = line.componente_id.product_id.id
                # Opcional: Si quieres que Odoo recalcule el precio basado en el producto,
                # podrías omitir 'price_unit' aquí o dejar que Odoo lo sobrescriba.
                # Si quieres mantener el precio del componente, asegúrate de que no se sobrescriba.
            order.order_line.create(vals)
        if self.capitulo_id.condiciones_legales:
            order.note = (order.note or '') + f"\n\nCondiciones del capítulo:\n{self.capitulo_id.condiciones_legales}"
        return {'type': 'ir.actions.act_window_close'}
