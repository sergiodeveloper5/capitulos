from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CapituloSeccionConfigurator(models.TransientModel):
    _name = 'capitulo.seccion.configurator'
    _description = 'Configurador de Secciones de Capítulo'
    
    sale_line_id = fields.Many2one('sale.order.line', string='Línea de Venta', required=True)
    order_id = fields.Many2one('sale.order', string='Pedido', required=True)
    capitulo_id = fields.Many2one('capitulo.contrato', string='Capítulo', required=True)
    
    seccion_line_ids = fields.One2many(
        'capitulo.seccion.configurator.line', 
        'configurator_id', 
        string='Secciones'
    )
    
    condiciones_particulares = fields.Text(
        string='Condiciones Particulares',
        help="Condiciones específicas para este presupuesto"
    )
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        
        # Cargar condiciones del capítulo si existen
        if res.get('capitulo_id'):
            capitulo = self.env['capitulo.contrato'].browse(res['capitulo_id'])
            if capitulo.condiciones_legales:
                res['condiciones_particulares'] = capitulo.condiciones_legales
        
        return res
    
    @api.model
    def create(self, vals):
        configurator = super().create(vals)
        configurator._create_seccion_lines()
        return configurator
    
    def _create_seccion_lines(self):
        """Crea las líneas de sección basadas en el capítulo seleccionado"""
        if not self.capitulo_id:
            return
            
        # Limpiar líneas existentes
        self.seccion_line_ids.unlink()
        
        # Crear líneas para cada sección del capítulo
        for seccion in self.capitulo_id.seccion_ids:
            self.env['capitulo.seccion.configurator.line'].create({
                'configurator_id': self.id,
                'seccion_id': seccion.id,
                'name': seccion.name,
                'incluir': True,  # Por defecto incluir todas
                'es_fija': True,  # Las secciones son fijas
            })
    
    def action_apply_configuration(self):
        """Aplica la configuración de secciones al presupuesto"""
        self.ensure_one()
        
        # Validar que al menos una sección esté seleccionada
        secciones_incluidas = self.seccion_line_ids.filtered('incluir')
        if not secciones_incluidas:
            raise UserError("Debe seleccionar al menos una sección para incluir en el presupuesto.")
        
        # Eliminar líneas existentes del capítulo si las hay
        self._remove_existing_capitulo_lines()
        
        # Crear las nuevas líneas estructuradas
        self._create_structured_lines(secciones_incluidas)
        
        # Marcar la línea principal como configurada
        seccion_names = ', '.join(secciones_incluidas.mapped('name'))
        self.sale_line_id.write({
            'seccion_configurada': seccion_names,
            'name': f"{self.capitulo_id.name} ({seccion_names})"
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _remove_existing_capitulo_lines(self):
        """Elimina líneas existentes del capítulo en el presupuesto"""
        existing_lines = self.order_id.order_line.filtered(
            lambda l: l.capitulo_id == self.capitulo_id and l.id != self.sale_line_id.id
        )
        if existing_lines:
            existing_lines.with_context(from_capitulo_wizard=True).unlink()
    
    def _create_structured_lines(self, secciones_incluidas):
        """Crea las líneas estructuradas en el presupuesto"""
        SaleOrderLine = self.env['sale.order.line']
        sequence = self.sale_line_id.sequence + 1
        
        # Añadir encabezado del capítulo
        SaleOrderLine.with_context(from_capitulo_wizard=True).create({
            'order_id': self.order_id.id,
            'name': f"📋 ═══ {self.capitulo_id.name.upper()} ═══",
            'product_uom_qty': 0,
            'price_unit': 0,
            'display_type': 'line_section',
            'es_encabezado_capitulo': True,
            'capitulo_id': self.capitulo_id.id,
            'sequence': sequence,
        })
        sequence += 1
        
        # Crear líneas para cada sección incluida
        for seccion_line in secciones_incluidas:
            # Encabezado de sección
            SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': self.order_id.id,
                'name': f"🔒 === {seccion_line.name.upper()} === (SECCIÓN FIJA)",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'capitulo_id': self.capitulo_id.id,
                'sequence': sequence,
            })
            sequence += 1
            
            # Productos de la sección
            if seccion_line.product_line_ids:
                for product_line in seccion_line.product_line_ids:
                    if product_line.product_id:
                        SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                            'order_id': self.order_id.id,
                            'product_id': product_line.product_id.id,
                            'name': product_line.descripcion_personalizada or product_line.product_id.name,
                            'product_uom_qty': product_line.cantidad,
                            'price_unit': product_line.precio_unitario,
                            'product_uom': product_line.product_id.uom_id.id,
                            'capitulo_id': self.capitulo_id.id,
                            'sequence': sequence,
                        })
                        sequence += 1
            else:
                # Línea informativa si no hay productos
                SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                    'order_id': self.order_id.id,
                    'name': "(Sin productos añadidos en esta sección)",
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'display_type': 'line_note',
                    'capitulo_id': self.capitulo_id.id,
                    'sequence': sequence,
                })
                sequence += 1
        
        # Añadir condiciones particulares si existen
        if self.condiciones_particulares:
            SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': self.order_id.id,
                'name': "=== CONDICIONES PARTICULARES ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'capitulo_id': self.capitulo_id.id,
                'sequence': sequence,
            })
            sequence += 1
            
            SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': self.order_id.id,
                'name': self.condiciones_particulares,
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_note',
                'capitulo_id': self.capitulo_id.id,
                'sequence': sequence,
            })

class CapituloSeccionConfiguratorLine(models.TransientModel):
    _name = 'capitulo.seccion.configurator.line'
    _description = 'Línea del Configurador de Secciones'
    _order = 'sequence, name'
    
    configurator_id = fields.Many2one('capitulo.seccion.configurator', ondelete='cascade')
    seccion_id = fields.Many2one('capitulo.seccion', string='Sección Original')
    name = fields.Char(string='Nombre de la Sección', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    incluir = fields.Boolean(string='Incluir en Presupuesto', default=True)
    es_fija = fields.Boolean(string='Sección Fija', default=True)
    
    product_line_ids = fields.One2many(
        'capitulo.seccion.configurator.product', 
        'seccion_line_id', 
        string='Productos'
    )
    
    @api.model
    def create(self, vals):
        line = super().create(vals)
        if line.seccion_id:
            line._load_products_from_seccion()
        return line
    
    def _load_products_from_seccion(self):
        """Carga los productos de la sección original"""
        if not self.seccion_id:
            return
            
        for product_line in self.seccion_id.product_line_ids:
            self.env['capitulo.seccion.configurator.product'].create({
                'seccion_line_id': self.id,
                'product_id': product_line.product_id.id,
                'descripcion_personalizada': product_line.descripcion_personalizada,
                'cantidad': product_line.cantidad,
                'precio_unitario': product_line.precio_unitario,
            })

class CapituloSeccionConfiguratorProduct(models.TransientModel):
    _name = 'capitulo.seccion.configurator.product'
    _description = 'Producto del Configurador de Secciones'
    
    seccion_line_id = fields.Many2one('capitulo.seccion.configurator.line', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Producto')
    descripcion_personalizada = fields.Char(string='Descripción Personalizada')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    precio_unitario = fields.Float(string='Precio Unitario')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.precio_unitario = self.product_id.list_price