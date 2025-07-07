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
    
    def unlink_seccion(self):
        """Elimina la sección si no es fija"""
        if self.es_fija:
            raise UserError("No se pueden eliminar secciones fijas")
        return self.unlink()

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

    # Modo de operación
    modo_creacion = fields.Selection([
        ('existente', 'Usar Capítulo Existente'),
        ('nuevo', 'Crear Nuevo Capítulo')
    ], string='Modo de Creación', default='existente', required=True)
    
    # Campos para capítulo existente
    capitulo_id = fields.Many2one('capitulo.contrato', string='Capítulo')
    
    # Campos para crear nuevo capítulo
    nuevo_capitulo_nombre = fields.Char(string='Nombre del Capítulo')
    nuevo_capitulo_descripcion = fields.Text(string='Descripción del Capítulo')
    
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

    @api.onchange('modo_creacion')
    def onchange_modo_creacion(self):
        """Limpiar campos cuando cambia el modo de creación"""
        if self.modo_creacion == 'existente':
            self.nuevo_capitulo_nombre = False
            self.nuevo_capitulo_descripcion = False
        elif self.modo_creacion == 'nuevo':
            self.capitulo_id = False
        
        # Limpiar secciones en todos los casos
        self.seccion_ids = [(5, 0, 0)]
    
    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """Carga las secciones del capítulo seleccionado"""
        if self.modo_creacion != 'existente':
            return
            
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
    
    def _obtener_o_crear_capitulo(self):
        """Obtiene un capítulo existente o crea uno nuevo según el modo"""
        if self.modo_creacion == 'existente':
            if not self.capitulo_id:
                raise UserError("Debe seleccionar un capítulo existente")
            return self.capitulo_id
        
        elif self.modo_creacion == 'nuevo':
            if not self.nuevo_capitulo_nombre:
                raise UserError("Debe especificar un nombre para el nuevo capítulo")
            
            # Crear nuevo capítulo
            capitulo_vals = {
                'name': self.nuevo_capitulo_nombre,
                'description': self.nuevo_capitulo_descripcion,
                'condiciones_legales': self.condiciones_particulares,
                'es_plantilla': False,
            }
            
            # Crear secciones del capítulo
            secciones_vals = []
            for seccion_wizard in self.seccion_ids.filtered('incluir'):
                lineas_vals = []
                for linea_wizard in seccion_wizard.line_ids.filtered('incluir'):
                    lineas_vals.append((0, 0, {
                        'product_id': linea_wizard.product_id.id,
                        'cantidad': linea_wizard.cantidad,
                        'precio_unitario': linea_wizard.precio_unitario,
                        'sequence': linea_wizard.sequence,
                        'descripcion_personalizada': linea_wizard.descripcion_personalizada,
                        'es_opcional': linea_wizard.es_opcional,
                    }))
                
                if lineas_vals:  # Solo crear sección si tiene productos
                    secciones_vals.append((0, 0, {
                        'name': seccion_wizard.name,
                        'sequence': seccion_wizard.sequence,
                        'es_fija': seccion_wizard.es_fija,
                        'product_line_ids': lineas_vals,
                    }))
            
            capitulo_vals['seccion_ids'] = secciones_vals
            return self.env['capitulo.contrato'].create(capitulo_vals)
        
        else:
            raise UserError("Modo de creación no válido")

    def add_to_order(self):
        """Añade las secciones y productos seleccionados al pedido de venta"""
        self.ensure_one()
        
        if not self.order_id:
            raise UserError("No se encontró el pedido de venta")

        # Crear o obtener el capítulo según el modo
        capitulo = self._obtener_o_crear_capitulo()
        
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
        order.write({'capitulo_ids': [(4, capitulo.id)]})

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
    
    def add_seccion(self):
        """Añade una nueva sección al wizard"""
        self.ensure_one()
        
        # Obtener la siguiente secuencia
        max_sequence = max([s.sequence for s in self.seccion_ids] or [0])
        
        # Añadir nueva sección directamente a la lista
        self.write({
            'seccion_ids': [(0, 0, {
                'name': 'Nueva Sección',
                'sequence': max_sequence + 10,
                'es_fija': False,
                'incluir': True,
            })]
        })
        
        # Retornar acción para refrescar la vista
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }
    

    
    def add_another_chapter(self):
        """Añade el capítulo actual y abre el wizard para añadir otro"""
        self.ensure_one()
        
        # Primero añadir el capítulo actual
        self.add_to_order()
        
        # Crear un nuevo wizard para añadir otro capítulo
        new_wizard = self.create({
            'order_id': self.order_id.id,
            'modo_creacion': 'existente',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': new_wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.order_id.id}
        }