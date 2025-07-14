from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    capitulo_ids = fields.Many2many(
        'capitulo.contrato', 
        string='Capítulos Aplicados',
        help="Capítulos técnicos aplicados a este pedido de venta"
    )
    
    capitulos_agrupados = fields.Text(
        string='Capítulos Agrupados',
        compute='_compute_capitulos_agrupados',
        help="JSON con las líneas agrupadas por capítulo para el widget acordeón"
    )
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo', 'order_line.es_encabezado_seccion')
    def _compute_capitulos_agrupados(self):
        """Agrupa las líneas del pedido por capítulos para mostrar en acordeón"""
        import json
        
        for order in self:
            capitulos_dict = {}
            current_capitulo_name = None
            current_seccion_name = None
            
            for line in order.order_line.sorted('sequence'):
                if line.es_encabezado_capitulo:
                    # Nuevo capítulo
                    current_capitulo_name = line.name
                    capitulos_dict[current_capitulo_name] = {
                        'sections': {},
                        'total': 0.0
                    }
                    current_seccion_name = None
                    
                elif line.es_encabezado_seccion and current_capitulo_name:
                    # Nueva sección dentro del capítulo actual
                    current_seccion_name = line.name
                    capitulos_dict[current_capitulo_name]['sections'][current_seccion_name] = {
                        'lines': []
                    }
                    
                elif current_capitulo_name and current_seccion_name:
                    # Producto dentro de la sección actual
                    line_data = {
                        'sequence': line.sequence,
                        'product_name': line.product_id.name if line.product_id else '',
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.name if line.product_uom else '',
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal
                    }
                    capitulos_dict[current_capitulo_name]['sections'][current_seccion_name]['lines'].append(line_data)
                    capitulos_dict[current_capitulo_name]['total'] += line.price_subtotal
            
            order.capitulos_agrupados = json.dumps(capitulos_dict) if capitulos_dict else '{}'
    
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
    
    def toggle_capitulo_collapse(self, capitulo_index):
        """Alterna el estado colapsado/expandido de un capítulo"""
        import json
        
        self.ensure_one()
        capitulos = json.loads(self.capitulos_agrupados or '[]')
        
        if 0 <= capitulo_index < len(capitulos):
            capitulos[capitulo_index]['collapsed'] = not capitulos[capitulo_index].get('collapsed', True)
            self.capitulos_agrupados = json.dumps(capitulos)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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
        # Si se está modificando desde el wizard de capítulos, permitir la modificación
        if self.env.context.get('from_capitulo_wizard'):
            return super().write(vals)
            
        protected_fields = ['name', 'product_id', 'product_uom_qty', 'price_unit', 'sequence', 'display_type']
        
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
    
    @api.model
    def create(self, vals):
        """Controla la creación de nuevas líneas cuando hay capítulos estructurados"""
        # Si se está creando desde el wizard de capítulos, permitir la creación
        if self.env.context.get('from_capitulo_wizard'):
            return super().create(vals)
        
        # Bloquear la creación manual de encabezados de capítulos y secciones
        if vals.get('es_encabezado_capitulo') or vals.get('es_encabezado_seccion'):
            raise UserError(
                "No se pueden crear encabezados de capítulos o secciones manualmente.\n"
                "Use el botón 'Gestionar Capítulos' para añadir capítulos estructurados."
            )
        
        # Bloquear la creación de líneas de tipo 'line_section' que no sean productos normales
        if vals.get('display_type') in ['line_section', 'line_note'] and not vals.get('product_id'):
            order_id = vals.get('order_id')
            if order_id:
                order = self.env['sale.order'].browse(order_id)
                existing_headers = order.order_line.filtered(
                    lambda l: l.es_encabezado_capitulo or l.es_encabezado_seccion
                )
                if existing_headers:
                    raise UserError(
                        "No se pueden añadir secciones o notas manualmente cuando el presupuesto tiene capítulos estructurados.\n"
                        "Use el botón 'Gestionar Capítulos' para gestionar la estructura."
                    )
        
        return super().create(vals)