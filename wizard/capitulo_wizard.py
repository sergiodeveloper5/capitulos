from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

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
    
    def unlink(self):
        """Previene la eliminación de secciones fijas"""
        for seccion in self:
            if seccion.es_fija:
                raise UserError(
                    f"No se puede eliminar la sección '{seccion.name}' porque es una sección fija.\n"
                    "Las secciones fijas son elementos estructurales del capítulo."
                )
        return super().unlink()
    
    def write(self, vals):
        """Previene la modificación de secciones fijas"""
        protected_fields = ['name', 'sequence']
        
        for seccion in self:
            if seccion.es_fija:
                # Verificar si se está intentando modificar campos protegidos
                for field in protected_fields:
                    if field in vals:
                        raise UserError(
                            f"No se puede modificar la sección fija '{seccion.name}'.\n"
                            f"Las secciones fijas son elementos estructurales del capítulo."
                        )
        
        return super().write(vals)
    
    @api.constrains('name')
    def _check_name(self):
        """Valida que el nombre de la sección no esté vacío"""
        for record in self:
            if not record.name or not record.name.strip():
                raise UserError("El nombre de la sección es obligatorio y no puede estar vacío.")
    
    @api.model
    def create(self, vals):
        """Asegura que se establezcan valores por defecto apropiados"""
        original_name = vals.get('name')
        _logger.info(f"Creando sección con nombre original: '{original_name}'")
        
        # Solo establecer 'Nueva Sección' si realmente no hay nombre
        if not vals.get('name') or vals.get('name').strip() == '':
            vals['name'] = 'Nueva Sección'
            _logger.warning(f"Nombre vacío detectado, estableciendo 'Nueva Sección'. Nombre original: '{original_name}'")
        
        if not vals.get('sequence'):
            vals['sequence'] = 10
        if 'incluir' not in vals:
            vals['incluir'] = True
        if 'es_fija' not in vals:
            vals['es_fija'] = False
            
        _logger.info(f"Creando sección final con nombre: '{vals['name']}', es_fija: {vals['es_fija']}")
        return super().create(vals)
    
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
    product_id = fields.Many2one('product.product', string='Producto')
    descripcion_personalizada = fields.Char(string='Descripción Personalizada')
    cantidad = fields.Float(string='Cantidad', default=1, required=True)
    precio_unitario = fields.Float(string='Precio', default=0.0)
    incluir = fields.Boolean(string='Incluir', default=True)
    es_opcional = fields.Boolean(string='Opcional', default=False)
    sequence = fields.Integer(string='Secuencia', default=10)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza el precio unitario cuando se selecciona un producto"""
        if self.product_id:
            self.precio_unitario = self.product_id.list_price
        else:
            self.precio_unitario = 0.0

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
        
        _logger.info("default_get: inicializando wizard")
        return res
    
    def write(self, vals):
        """Override write para verificar integridad después de cambios"""
        # Evitar recursión infinita con una bandera de contexto
        if self.env.context.get('skip_integrity_check'):
            return super().write(vals)
            
        result = super().write(vals)
        # Verificar integridad de secciones después de cualquier cambio
        if 'seccion_ids' in vals or 'modo_creacion' in vals:
            self._verificar_integridad_secciones()
        return result

    @api.onchange('modo_creacion')
    def onchange_modo_creacion(self):
        """Limpiar campos cuando cambia el modo de creación"""
        if self.modo_creacion == 'existente':
            self.nuevo_capitulo_nombre = False
            self.nuevo_capitulo_descripcion = False
            # Limpiar secciones al cambiar a modo existente usando contexto para evitar recursión
            self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
        elif self.modo_creacion == 'nuevo':
            self.capitulo_id = False
            # Solo crear secciones predefinidas si no existen ya
            if not self.seccion_ids:
                self._crear_secciones_predefinidas()
    
    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """Carga las secciones del capítulo seleccionado"""
        if self.modo_creacion != 'existente':
            return
            
        # Limpiar secciones usando contexto para evitar recursión
        self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
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
    

    
    def _verificar_integridad_secciones(self):
        """Verifica y restaura la integridad de las secciones predefinidas solo si es necesario"""
        # Solo verificar si hay secciones con nombres vacíos o inválidos
        secciones_actuales = [s.name for s in self.seccion_ids if s.name and s.name.strip()]
        
        # Si hay secciones con nombres vacíos o "Nueva Sección", recrear solo si no hay secciones válidas
        if any(name == 'Nueva Sección' for name in secciones_actuales) or len(secciones_actuales) == 0:
            self._crear_secciones_predefinidas()
            return True
        return False
    
    def action_open_templates(self):
        """Abre la lista de plantillas disponibles"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Plantillas de Capítulos',
            'res_model': 'capitulo.contrato',
            'view_mode': 'list,form',
            'domain': [('es_plantilla', '=', True)],
            'context': {'search_default_es_plantilla': 1},
            'target': 'new',
        }
    
    def action_create_template(self):
        """Crea una nueva plantilla"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Nueva Plantilla',
            'res_model': 'capitulo.contrato',
            'view_mode': 'form',
            'context': {'default_es_plantilla': True},
            'target': 'new',
        }
    
    def action_delete_template(self):
        """Elimina la plantilla seleccionada"""
        if not self.capitulo_id or not self.capitulo_id.es_plantilla:
            raise UserError("Solo se pueden eliminar plantillas.")
        
        # Llamar al método de eliminación de la plantilla
        result = self.capitulo_id.action_eliminar_plantilla_forzado()
        
        # Limpiar el campo capitulo_id después de la eliminación
        self.capitulo_id = False
        
        return {
              'type': 'ir.actions.client',
              'tag': 'display_notification',
              'params': {
                  'title': 'Plantilla Eliminada',
                  'message': 'La plantilla ha sido eliminada correctamente.',
                  'type': 'success',
                  'sticky': False,
              }
          }
    
    def action_convert_to_template(self):
        """Convierte el capítulo seleccionado en plantilla"""
        if not self.capitulo_id:
            raise UserError("Debe seleccionar un capítulo para convertir en plantilla.")
        
        if self.capitulo_id.es_plantilla:
            raise UserError("El capítulo seleccionado ya es una plantilla.")
        
        # Convertir en plantilla
        self.capitulo_id.write({'es_plantilla': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Capítulo Convertido',
                'message': f'El capítulo "{self.capitulo_id.name}" ha sido convertido en plantilla correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _crear_secciones_predefinidas(self):
        """Crea secciones predefinidas básicas"""
        secciones_predefinidas = [
            {'name': 'Alquiler', 'sequence': 10},
            {'name': 'Montaje', 'sequence': 20},
            {'name': 'Portes', 'sequence': 30},
            {'name': 'Otros Conceptos', 'sequence': 40},
        ]
        
        # Limpiar secciones existentes primero usando contexto para evitar recursión
        self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
        
        # Determinar si las secciones deben ser fijas según el modo
        es_fija = self.modo_creacion == 'existente'
        
        secciones_vals = []
        for seccion_data in secciones_predefinidas:
            vals = {
                'name': seccion_data['name'],
                'sequence': seccion_data['sequence'],
                'es_fija': es_fija,  # Fijas solo en modo existente
                'incluir': True,
                'line_ids': [],
            }
            secciones_vals.append((0, 0, vals))
        
        # Crear secciones usando contexto para evitar recursión
        self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
        
        # Verificar que se crearon correctamente
        try:
            # Forzar flush para asegurar que los datos se escriban
            self.env.flush_all()
        except Exception as e:
            _logger.error(f"Error al confirmar secciones: {e}")
            # Intentar recrear si hay error
            self._recrear_secciones_seguro()
    
    def _recrear_secciones_seguro(self):
        """Método seguro para recrear secciones en caso de error"""
        try:
            # Crear secciones una por una para mayor control
            secciones_predefinidas = [
                {'name': 'Alquiler', 'sequence': 10},
                {'name': 'Montaje', 'sequence': 20},
                {'name': 'Portes', 'sequence': 30},
                {'name': 'Otros Conceptos', 'sequence': 40},
            ]
            
            # Limpiar completamente usando contexto para evitar recursión
            self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
            
            # Determinar si las secciones deben ser fijas según el modo
            es_fija = self.modo_creacion == 'existente'
            
            # Crear todas las secciones de una vez
            secciones_vals = []
            for seccion_data in secciones_predefinidas:
                try:
                    seccion_vals = (0, 0, {
                        'name': seccion_data['name'],
                        'sequence': seccion_data['sequence'],
                        'es_fija': es_fija,
                        'incluir': True,
                        'line_ids': [],
                    })
                    secciones_vals.append(seccion_vals)
                except Exception as e:
                    _logger.error(f"Error preparando sección '{seccion_data['name']}': {e}")
            
            # Crear todas las secciones usando contexto para evitar recursión
            if secciones_vals:
                self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
                    
        except Exception as e:
            _logger.error(f"Error en recreación segura: {e}")
    
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
                    'precio_unitario': linea.precio_unitario,
                    'sequence': linea.sequence,
                    'incluir': True,
                    'es_opcional': linea.es_opcional,
                }))
            
            secciones_vals.append((0, 0, {
                'name': seccion.name,
                'sequence': seccion.sequence,
                'es_fija': True,  # Todas las secciones de capítulos existentes son fijas
                'incluir': True,
                'line_ids': lineas_vals,
            }))
        
        # Cargar secciones usando contexto para evitar recursión
        self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
    
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
                
                # Crear sección siempre (incluso si no tiene productos)
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
        
        # Verificar integridad de secciones antes de proceder
        self._verificar_integridad_secciones()
        
        # Validar datos del wizard antes de proceder
        self._validate_wizard_data()

        # Crear o obtener el capítulo según el modo
        capitulo = self._obtener_o_crear_capitulo()
        
        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # Marcar todas las secciones como fijas después de añadir al pedido
        for seccion in self.seccion_ids:
            seccion.es_fija = True
        
        # Añadir título del capítulo como encabezado principal
        nombre_capitulo = capitulo.name if self.modo_creacion == 'existente' else self.nuevo_capitulo_nombre
        SaleOrderLine.with_context(from_capitulo_wizard=True).create({
            'order_id': order.id,
            'name': f"📋 ═══ {nombre_capitulo.upper()} ═══",
            'product_uom_qty': 0,
            'price_unit': 0,
            'display_type': 'line_section',
            'es_encabezado_capitulo': True,
        })
        
        # Crear líneas de pedido organizadas por secciones
        for seccion in self.seccion_ids.filtered('incluir'):
            # Añadir línea de sección como separador (siempre, incluso si no tiene productos)
            section_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': f"=== {seccion.name.upper()} ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
            })
            
            # Si la sección es fija, marcar la línea como no editable
            if seccion.es_fija:
                section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
            
            # Añadir productos de la sección que estén marcados para incluir y tengan producto seleccionado
            productos_incluidos = seccion.line_ids.filtered(lambda l: l.incluir and l.product_id)
            
            if productos_incluidos:
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
                    
                    product_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create(vals)
                    
                    # Si la sección es fija, añadir una nota indicativa
                    if seccion.es_fija:
                        product_line.write({'name': f"🔒 {descripcion} (No modificable)"})
            else:
                # Si no hay productos, añadir una línea informativa
                SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                    'order_id': order.id,
                    'name': "(Sin productos añadidos en esta sección)",
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'display_type': 'line_note',
                })

        # Añadir capítulo a la lista de capítulos aplicados
        order.write({'capitulo_ids': [(4, capitulo.id)]})

        # Añadir condiciones particulares si existen
        if self.condiciones_particulares:
            # Añadir sección de condiciones particulares
            SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': "=== CONDICIONES PARTICULARES ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
            })
            
            # Añadir las condiciones como nota
            SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': self.condiciones_particulares,
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_note',
            })

        return {'type': 'ir.actions.act_window_close'}
    
    def add_seccion(self):
        """Función deshabilitada - No se pueden añadir más secciones"""
        raise UserError(
            "No se pueden añadir nuevas secciones.\n"
            "Las secciones están predefinidas y son fijas para mantener la estructura del capítulo."
        )
    

    
    def _validate_wizard_data(self):
        """Valida que los datos del wizard sean correctos antes de proceder"""
        if self.modo_creacion == 'existente' and not self.capitulo_id:
            raise UserError("Debe seleccionar un capítulo existente.")
        
        if self.modo_creacion == 'nuevo' and not self.nuevo_capitulo_nombre:
            raise UserError("Debe especificar un nombre para el nuevo capítulo.")
        
        # Validar que las secciones tengan nombres válidos
        for seccion in self.seccion_ids:
            if not seccion.name or not seccion.name.strip():
                raise UserError(f"La sección en la posición {seccion.sequence} no tiene un nombre válido.")
        
        # Validar que al menos una sección esté marcada para incluir
        secciones_incluidas = self.seccion_ids.filtered('incluir')
        if not secciones_incluidas:
            raise UserError("Debe seleccionar al menos una sección para incluir en el presupuesto.")
    
    def add_another_chapter(self):
        """Añade el capítulo actual y abre el wizard para añadir otro"""
        self.ensure_one()
        
        # Validar datos antes de proceder
        self._validate_wizard_data()
        
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