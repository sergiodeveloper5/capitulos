from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    capitulo_ids = fields.Many2many(
        'capitulo.contrato',
        'sale_order_capitulo_rel',
        'sale_order_id',
        'capitulo_id',
        string='Capítulos Aplicados',
        help="Capítulos técnicos aplicados a este pedido de venta"
    )
    
    def action_add_capitulo(self):
        """Acción para abrir el configurador de capítulos"""
        self.ensure_one()
        
        # Abrir vista de productos filtrada por capítulos
        return {
            'type': 'ir.actions.act_window',
            'name': 'Seleccionar Capítulo',
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': [('is_capitulo', '=', True)],
            'context': {
                'default_is_capitulo': True,
                'default_type': 'service',
                'sale_order_id': self.id,
                'search_default_capitulos': 1
            },
            'target': 'new',
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
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato',
        string='Capítulo',
        help="Capítulo al que pertenece esta línea",
        column='capitulo_id'
    )
    
    seccion_configurada = fields.Char(
        string='Sección Configurada',
        help="Sección del capítulo configurada para esta línea"
    )
    
    es_linea_capitulo = fields.Boolean(
        string='Es Línea de Capítulo',
        compute='_compute_es_linea_capitulo',
        store=True
    )
    
    @api.depends('product_id')
    def _compute_es_linea_capitulo(self):
        for line in self:
            line.es_linea_capitulo = bool(line.product_id and line.product_id.is_capitulo)
    
    @api.onchange('product_id')
    def _onchange_product_id_capitulo(self):
        """Cuando se selecciona un capítulo, abrir configurador de secciones"""
        if self.product_id and self.product_id.is_capitulo:
            # Establecer el capítulo
            capitulo = self.env['capitulo.contrato'].search([('product_tmpl_id', '=', self.product_id.id)], limit=1)
            if capitulo:
                self.capitulo_id = capitulo.id
                # Abrir configurador de secciones
                return self._open_seccion_configurator()
    
    def _open_seccion_configurator(self):
        """Abre el configurador de secciones para el capítulo"""
        if not self.capitulo_id:
            return
            
        return {
            'type': 'ir.actions.act_window',
            'name': f'Configurar Secciones - {self.capitulo_id.name}',
            'res_model': 'capitulo.seccion.configurator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_line_id': self.id,
                'default_capitulo_id': self.capitulo_id.id,
                'default_order_id': self.order_id.id,
            }
        }
    
    def action_configure_secciones(self):
        """Acción para reconfigurar las secciones del capítulo"""
        self.ensure_one()
        if not self.es_linea_capitulo:
            return
        return self._open_seccion_configurator()
    
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