# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Capítulos del presupuesto
    capitulo_ids = fields.One2many('capitulo.capitulo', 'sale_order_id', 'Capítulos')
    
    # Campos calculados
    total_capitulos = fields.Monetary('Total Capítulos', compute='_compute_total_capitulos', store=True)
    tiene_capitulos = fields.Boolean('Tiene Capítulos', compute='_compute_tiene_capitulos')
    
    @api.depends('capitulo_ids.seccion_ids.total_seccion')
    def _compute_total_capitulos(self):
        for order in self:
            total = 0
            for capitulo in order.capitulo_ids:
                total += sum(seccion.total_seccion for seccion in capitulo.seccion_ids)
            order.total_capitulos = total
    
    @api.depends('capitulo_ids')
    def _compute_tiene_capitulos(self):
        for order in self:
            order.tiene_capitulos = bool(order.capitulo_ids)
    
    def action_create_capitulo(self):
        """Abrir wizard para crear nuevo capítulo"""
        return {
            'name': 'Crear Capítulo',
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_action_type': 'create',
            }
        }
    
    def action_use_template(self):
        """Abrir wizard para usar plantilla"""
        return {
            'name': 'Usar Plantilla de Capítulo',
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_action_type': 'template',
            }
        }
    
    def action_view_capitulos(self):
        """Ver capítulos del presupuesto"""
        action = self.env.ref('capitulos.action_capitulo_capitulo').read()[0]
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {
            'default_sale_order_id': self.id,
            'search_default_sale_order_id': self.id,
        }
        return action
    
    def generate_lines_from_capitulos(self):
        """Generar líneas de venta desde los capítulos"""
        # Eliminar líneas existentes de capítulos
        lines_to_remove = self.order_line.filtered(lambda l: l.name and l.name.startswith('['))
        lines_to_remove.unlink()
        
        # Crear nuevas líneas desde capítulos
        for capitulo in self.capitulo_ids:
            # Línea de sección para el capítulo
            self.env['sale.order.line'].create({
                'order_id': self.id,
                'display_type': 'line_section',
                'name': f"{capitulo.name} - {capitulo.description or ''}",
            })
            
            for seccion in capitulo.seccion_ids:
                # Línea de nota para la sección
                self.env['sale.order.line'].create({
                    'order_id': self.id,
                    'display_type': 'line_note',
                    'name': f"  {seccion.name}",
                })
                
                # Líneas de productos
                for producto in seccion.producto_ids:
                    self.env['sale.order.line'].create({
                        'order_id': self.id,
                        'product_id': producto.product_id.id,
                        'product_uom_qty': producto.quantity,
                        'price_unit': producto.price_unit,
                        'name': f"    {producto.product_id.name}",
                    })
    
    def action_generate_lines_from_capitulos(self):
        """Acción para generar líneas desde capítulos"""
        self.generate_lines_from_capitulos()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }