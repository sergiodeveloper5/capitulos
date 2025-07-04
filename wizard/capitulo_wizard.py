from odoo import models, fields, api
from odoo.exceptions import UserError

class CapituloWizardSeccion(models.TransientModel):
    _name = 'capitulo.wizard.seccion'
    _description = 'Sección del Wizard de Capítulo'
    _order = 'sequence, name'

    wizard_id = fields.Many2one('capitulo.wizard', ondelete='cascade')
    name = fields.Char(string='Nombre de la Sección', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    es_fija = fields.Boolean(string='Sección Fija', default=False)
    incluir = fields.Boolean(string='Incluir en Presupuesto', default=True)
    line_ids = fields.One2many('capitulo.wizard.line', 'seccion_id', string='Productos')

class CapituloWizardLine(models.TransientModel):
    _name = 'capitulo.wizard.line'
    _description = 'Línea de Configurador de capítulo'

    wizard_id = fields.Many2one('capitulo.wizard', ondelete='cascade')
    seccion_id = fields.Many2one('capitulo.wizard.seccion', string='Sección', ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True, string='Producto')
    descripcion_personalizada = fields.Char(string='Descripción Personalizada')
    cantidad = fields.Float(string='Cantidad', default=1, required=True)
    precio_unitario = fields.Float(string='Precio', related='product_id.list_price', readonly=False)
    incluir = fields.Boolean(string='Incluir', default=True)
    es_opcional = fields.Boolean(string='Opcional', default=False)
    sequence = fields.Integer(string='Secuencia', default=10)

class CapituloWizard(models.TransientModel):
    _name = 'capitulo.wizard'
    _description = 'Añadir Capítulo'

    capitulo_id = fields.Many2one('capitulo.contrato', required=True, string='Capítulo')
    order_id = fields.Many2one('sale.order', string='Pedido de Venta', required=True)
    seccion_ids = fields.One2many('capitulo.wizard.seccion', 'wizard_id', string='Secciones')
    condiciones_particulares = fields.Text(string='Condiciones Particulares')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # Obtener el pedido desde el contexto
        order_id = self.env.context.get('default_order_id') or self.env.context.get('active_id')
        if order_id and 'order_id' in fields:
            res['order_id'] = order_id
        return res

    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """Carga las secciones del capítulo seleccionado"""
        self.seccion_ids = [(5, 0, 0)]
        self.condiciones_particulares = ''
        
        if not self.capitulo_id:
            return
            
        # Cargar condiciones legales
        if self.capitulo_id.condiciones_legales:
            self.condiciones_particulares = self.capitulo_id.condiciones_legales
            
        # Cargar secciones del capítulo
        if self.capitulo_id.seccion_ids:
            self._cargar_secciones_existentes()
        else:
            # Si no hay secciones, crear secciones predefinidas
            self._crear_secciones_predefinidas()
    
    def _crear_secciones_predefinidas(self):
        """Crea secciones predefinidas básicas"""
        secciones_predefinidas = [
            {'name': 'Alquiler', 'sequence': 10, 'es_fija': True},
            {'name': 'Montaje', 'sequence': 20, 'es_fija': True},
            {'name': 'Portes', 'sequence': 30, 'es_fija': True},
            {'name': 'Otros Conceptos', 'sequence': 40, 'es_fija': False},
        ]
        
        secciones_vals = []
        for seccion_data in secciones_predefinidas:
            secciones_vals.append((0, 0, {
                'name': seccion_data['name'],
                'sequence': seccion_data['sequence'],
                'es_fija': seccion_data['es_fija'],
                'incluir': True,
                'line_ids': [],
            }))
        
        self.seccion_ids = secciones_vals
    
    def _cargar_secciones_existentes(self):
        """Carga las secciones existentes del capítulo"""
        secciones_vals = []
        for seccion in self.capitulo_id.seccion_ids:
            lineas_vals = []
            for linea in seccion.product_line_ids:
                lineas_vals.append((0, 0, {
                    'product_id': linea.product_id.id,
                    'descripcion_personalizada': linea.descripcion_personalizada,
                    'cantidad': linea.cantidad,
                    'sequence': linea.sequence,
                    'incluir': True,
                    'es_opcional': linea.es_opcional,
                }))
            
            secciones_vals.append((0, 0, {
                'name': seccion.name,
                'sequence': seccion.sequence,
                'es_fija': seccion.es_fija,
                'incluir': True,
                'line_ids': lineas_vals,
            }))
        
        self.seccion_ids = secciones_vals

    def add_to_order(self):
        """Añade las secciones y productos seleccionados al pedido de venta"""
        self.ensure_one()
        
        if not self.order_id:
            raise UserError("No se encontró el pedido de venta")

        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # Crear líneas de pedido organizadas por secciones
        for seccion in self.seccion_ids.filtered('incluir'):
            # Solo añadir sección si tiene productos
            productos_incluidos = seccion.line_ids.filtered('incluir')
            if productos_incluidos:
                # Añadir línea de sección como separador (no modificable)
                section_line = SaleOrderLine.create({
                    'order_id': order.id,
                    'name': f"=== {seccion.name.upper()} ===",
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'display_type': 'line_section',
                })
                
                # Si la sección es fija, marcar la línea como no editable
                if seccion.es_fija:
                    section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
                
                # Añadir productos de la sección
                for line in productos_incluidos:
                    descripcion = line.descripcion_personalizada or line.product_id.name
                    
                    vals = {
                        'order_id': order.id,
                        'product_id': line.product_id.id,
                        'name': descripcion,
                        'price_unit': line.precio_unitario,
                        'product_uom_qty': line.cantidad,
                        'product_uom': line.product_id.uom_id.id,
                    }
                    
                    product_line = SaleOrderLine.create(vals)
                    
                    # Si la sección es fija, añadir una nota indicativa
                    if seccion.es_fija:
                        product_line.write({'name': f"🔒 {descripcion} (No modificable)"})

        # Añadir capítulo a la lista de capítulos aplicados
        order.write({'capitulo_ids': [(4, self.capitulo_id.id)]})

        # Añadir condiciones particulares si existen
        if self.condiciones_particulares:
            # Añadir sección de condiciones particulares
            SaleOrderLine.create({
                'order_id': order.id,
                'name': "=== CONDICIONES PARTICULARES ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
            })
            
            # Añadir las condiciones como nota
            SaleOrderLine.create({
                'order_id': order.id,
                'name': self.condiciones_particulares,
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_note',
            })

        return {'type': 'ir.actions.act_window_close'}