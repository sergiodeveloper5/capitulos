from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CapituloWizardSeccion(models.TransientModel):
    _name = 'capitulo.wizard.seccion'
    _description = 'Sección del Wizard de Capítulo'
    _order = 'sequence, name'

    wizard_id = fields.Many2one('capitulo.wizard', ondelete='cascade')
    name = fields.Char(string='Nombre de la Sección', required=True, default='Nueva Sección')
    sequence = fields.Integer(string='Secuencia', default=10)
    es_fija = fields.Boolean(string='Sección Fija', default=False)
    incluir = fields.Boolean(string='Incluir en Presupuesto', default=False)
    line_ids = fields.One2many('capitulo.wizard.line', 'seccion_id', string='Productos')
    
    # Campo para filtrar productos por categoría
    product_category_id = fields.Many2one(
        'product.category', 
        string='Categoría de Productos',
        required=True,
        help='Debe seleccionar una categoría para poder añadir productos a esta sección'
    )
    
    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        """Limpiar productos cuando se cambie la categoría"""
        if self.product_category_id:
            # Si hay productos existentes de una categoría diferente, avisar al usuario
            if self.line_ids:
                productos_diferentes = self.line_ids.filtered(
                    lambda l: l.product_id and l.product_id.categ_id.id not in self.product_category_id.child_ids.ids + [self.product_category_id.id]
                )
                if productos_diferentes:
                    # Limpiar productos que no pertenecen a la nueva categoría
                    self.line_ids = [(5, 0, 0)]  # Eliminar todas las líneas
                    return {
                        'warning': {
                            'title': 'Categoría cambiada',
                            'message': 'Se han eliminado los productos existentes porque no pertenecen a la nueva categoría seleccionada.'
                        }
                    }
    
    @api.constrains('line_ids', 'product_category_id')
    def _check_category_before_products(self):
        """Valida que se haya seleccionado una categoría antes de añadir productos"""
        for record in self:
            if record.line_ids and not record.product_category_id:
                raise UserError(
                    "Debe seleccionar una categoría de productos antes de añadir productos a la sección.\n\n"
                    "Para añadir productos:\n"
                    "1. Seleccione una categoría de productos\n"
                    "2. Luego podrá añadir productos de esa categoría"
                )
    
    @api.constrains('product_id', 'seccion_id')
    def _check_product_category(self):
        """Valida que el producto pertenezca a la categoría seleccionada en la sección"""
        for record in self:
            if record.product_id and record.seccion_id and record.seccion_id.product_category_id:
                categoria_seccion = record.seccion_id.product_category_id
                categoria_producto = record.product_id.categ_id
                
                # Verificar si el producto pertenece a la categoría o a una subcategoría
                if categoria_producto.id not in categoria_seccion.child_ids.ids + [categoria_seccion.id]:
                    raise UserError(
                        f"El producto '{record.product_id.name}' no pertenece a la categoría '{categoria_seccion.name}' "
                        f"seleccionada para esta sección.\n\n"
                        f"Categoría del producto: {categoria_producto.name}\n"
                        f"Categoría requerida: {categoria_seccion.name}"
                    )
    
    @api.model
    def create(self, vals):
        """Asegurar que siempre se cree con un nombre válido"""
        if not vals.get('name') or not vals.get('name').strip():
            vals['name'] = 'Nueva Sección'
        _logger.info(f"Creando sección: {vals.get('name')}")
        return super().create(vals)
    
    def unlink(self):
        """Permite la eliminación de secciones en el wizard"""
        return super().unlink()
    
    def write(self, vals):
        """Permite la modificación de secciones en el wizard"""
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
        """Elimina la sección"""
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
    incluir = fields.Boolean(string='Incluir', default=False)
    es_opcional = fields.Boolean(string='Opcional', default=False)
    sequence = fields.Integer(string='Secuencia', default=10)
    
    @api.model
    def create(self, vals):
        """Asegurar que siempre se establezca la relación wizard_id correctamente"""
        # Si no se proporciona wizard_id pero sí seccion_id, obtenerlo de la sección
        if not vals.get('wizard_id') and vals.get('seccion_id'):
            seccion = self.env['capitulo.wizard.seccion'].browse(vals['seccion_id'])
            if seccion.wizard_id:
                vals['wizard_id'] = seccion.wizard_id.id
                _logger.info(f"Estableciendo wizard_id={vals['wizard_id']} para nueva línea de producto")
        
        line = super().create(vals)
        _logger.info(f"Línea de producto creada: ID={line.id}, Producto={line.product_id.name if line.product_id else 'Sin producto'}, Sección={line.seccion_id.name if line.seccion_id else 'Sin sección'}")
        return line
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza el precio unitario cuando se selecciona un producto"""
        if self.product_id:
            self.precio_unitario = self.product_id.list_price
            # Automáticamente marcar como incluido (aunque no sea visible en la interfaz)
            self.incluir = True
            _logger.info(f"Producto seleccionado: {self.product_id.name}, Precio: {self.precio_unitario}, Auto-incluido: True")
        else:
            self.precio_unitario = 0.0
            self.incluir = False

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
    
    @api.model
    def create(self, vals):
        """Sobrescribir create para asegurar que las secciones se inicialicen correctamente"""
        _logger.info("=== Creando nuevo wizard ===")
        wizard = super().create(vals)
        
        # No crear secciones predefinidas - permitir al usuario añadir secciones manualmente
        _logger.info("Wizard creado sin secciones predefinidas")
        
        return wizard
    

    

    

    

    
    def write(self, vals):
        """Override write para manejar cambios"""
        # Evitar recursión infinita con una bandera de contexto
        if self.env.context.get('skip_integrity_check'):
            return super().write(vals)
            
        result = super().write(vals)
        return result

    @api.onchange('modo_creacion')
    def onchange_modo_creacion(self):
        """Limpiar campos cuando cambia el modo de creación"""
        _logger.info(f"=== onchange_modo_creacion: {self.modo_creacion} ===")
        
        if self.modo_creacion == 'existente':
            self.nuevo_capitulo_nombre = False
            self.nuevo_capitulo_descripcion = False
            # Limpiar secciones al cambiar a modo existente usando contexto para evitar recursión
            _logger.info("Limpiando secciones para modo existente")
            self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
        elif self.modo_creacion == 'nuevo':
            self.capitulo_id = False
            # Limpiar secciones para modo nuevo - permitir al usuario añadir secciones manualmente
            _logger.info(f"Modo nuevo - Limpiando secciones existentes: {len(self.seccion_ids)}")
            self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
    
    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """Carga las secciones del capítulo seleccionado"""
        if self.modo_creacion != 'existente':
            return
            
        # Limpiar secciones usando contexto para evitar recursión
        self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
        self.condiciones_particulares = ''
        
        if not self.capitulo_id:
            return
            
        # Cargar condiciones legales
        if self.capitulo_id.condiciones_legales:
            self.condiciones_particulares = self.capitulo_id.condiciones_legales
            
        # Cargar secciones del capítulo
        if self.capitulo_id.seccion_ids:
            self._cargar_secciones_existentes()
        # Si no hay secciones, dejar el wizard vacío para que el usuario añada secciones manualmente
    

    

    

    

    

    
    def _crear_secciones_predefinidas(self):
        """No crea secciones predefinidas - permite al usuario crear secciones manualmente"""
        _logger.info("=== Modo nuevo: No creando secciones predefinidas ===")
        
        # Limpiar secciones existentes usando contexto para evitar recursión
        _logger.info("Limpiando secciones existentes...")
        self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
        
        _logger.info("Wizard configurado sin secciones predefinidas - el usuario puede añadir secciones manualmente")
    
    def _recrear_secciones_seguro(self):
        """Método seguro para limpiar secciones en caso de error"""
        try:
            # Limpiar completamente usando contexto para evitar recursión
            self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
            _logger.info("Secciones limpiadas correctamente")
        except Exception as e:
            _logger.error(f"Error en limpieza de secciones: {e}")
    
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
                    'incluir': True,  # En modo existente, incluir automáticamente todos los productos
                    'es_opcional': linea.es_opcional,
                }))
            
            secciones_vals.append((0, 0, {
                'name': seccion.name,
                'sequence': seccion.sequence,
                'es_fija': True,  # Todas las secciones de capítulos existentes son fijas
                'incluir': True,  # En modo existente, incluir automáticamente todas las secciones
                'product_category_id': seccion.product_category_id.id if seccion.product_category_id else False,
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
            
            # Crear secciones del capítulo (solo las marcadas como incluir y que tienen productos)
            secciones_vals = []
            for seccion_wizard in self.seccion_ids.filtered(lambda s: s.incluir):
                # Solo incluir secciones marcadas como incluir y que tienen productos
                productos_con_producto = seccion_wizard.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    lineas_vals = []
                    for linea_wizard in productos_con_producto:
                        lineas_vals.append((0, 0, {
                            'product_id': linea_wizard.product_id.id,
                            'cantidad': linea_wizard.cantidad,
                            'precio_unitario': linea_wizard.precio_unitario,
                            'sequence': linea_wizard.sequence,
                            'descripcion_personalizada': linea_wizard.descripcion_personalizada,
                            'es_opcional': linea_wizard.es_opcional,
                        }))
                    
                    # Crear sección con productos
                    secciones_vals.append((0, 0, {
                        'name': seccion_wizard.name,
                        'sequence': seccion_wizard.sequence,
                        'es_fija': seccion_wizard.es_fija,
                        'product_category_id': seccion_wizard.product_category_id.id if seccion_wizard.product_category_id else False,
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
        
        # Debug: Verificar estado de las secciones antes de proceder
        _logger.info(f"=== DEBUG add_to_order ===")
        _logger.info(f"Wizard ID: {self.id}")
        _logger.info(f"Número de secciones: {len(self.seccion_ids)}")
        
        for seccion in self.seccion_ids:
            productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
            _logger.info(f"Sección: {seccion.name} (ID: {seccion.id}), Productos: {len(seccion.line_ids)}")
            _logger.info(f"  - Productos con producto seleccionado: {len(productos_con_producto)}")
            
            for line in seccion.line_ids:
                producto_nombre = line.product_id.name if line.product_id else 'Sin producto'
                _logger.info(f"    * ID: {line.id} | {producto_nombre}, Wizard ID: {line.wizard_id.id if line.wizard_id else 'NO ESTABLECIDO'}")
        

        
        # Validar datos del wizard antes de proceder
        self._validate_wizard_data()
        
        # Verificar si hay productos para añadir
        # En modo existente, incluir todas las secciones que tengan productos
        # En modo nuevo, solo las secciones marcadas como incluir
        total_productos_a_añadir = 0
        secciones_con_productos = []
        
        if self.modo_creacion == 'existente':
            # En modo existente, incluir todas las secciones que tengan productos
            for seccion in self.seccion_ids:
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        else:
            # En modo nuevo, solo secciones marcadas como incluir
            for seccion in self.seccion_ids.filtered(lambda s: s.incluir):
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        
        _logger.info(f"Secciones con productos: {len(secciones_con_productos)}")
        
        _logger.info(f"Total de productos que se van a añadir: {total_productos_a_añadir}")
        
        if total_productos_a_añadir == 0:
            if self.modo_creacion == 'existente':
                raise UserError(
                    "No hay productos en el capítulo seleccionado para añadir al presupuesto.\n\n"
                    "Para añadir productos:\n"
                    "1. Abra las secciones del capítulo\n"
                    "2. Añada productos usando 'Añadir una línea'\n"
                    "3. Seleccione el producto, cantidad y precio\n"
                    "4. Haga clic en 'Añadir al Presupuesto'"
                )
            else:
                raise UserError(
                    "No hay productos seleccionados para añadir al presupuesto.\n\n"
                    "Para añadir productos:\n"
                    "1. Marque las secciones que desea incluir usando el toggle 'Incluir'\n"
                    "2. Abra cada sección y añada productos usando 'Añadir una línea'\n"
                    "3. Seleccione el producto, cantidad y precio\n"
                    "4. Haga clic en 'Añadir al Presupuesto'"
                )

        # Crear o obtener el capítulo según el modo
        capitulo = self._obtener_o_crear_capitulo()
        
        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # Marcar todas las secciones como fijas después de añadir al pedido
        for seccion in self.seccion_ids:
            seccion.es_fija = True
        
        # Obtener la siguiente secuencia disponible
        max_sequence = max(order.order_line.mapped('sequence')) if order.order_line else 0
        current_sequence = max_sequence + 10
        
        # Añadir título del capítulo como encabezado principal
        nombre_capitulo = capitulo.name if self.modo_creacion == 'existente' else self.nuevo_capitulo_nombre
        SaleOrderLine.with_context(from_capitulo_wizard=True).create({
            'order_id': order.id,
            'name': f"📋 ═══ {nombre_capitulo.upper()} ═══",
            'product_uom_qty': 0,
            'price_unit': 0,
            'display_type': 'line_section',
            'es_encabezado_capitulo': True,
            'sequence': current_sequence,
        })
        current_sequence += 10
        
        # Crear líneas de pedido organizadas por secciones (solo secciones que tienen productos)
        for seccion in secciones_con_productos:
            # Añadir línea de sección como separador (siempre, incluso si no tiene productos)
            section_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': f"=== {seccion.name.upper()} ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'sequence': current_sequence,
            })
            current_sequence += 10
            
            # Si la sección es fija, marcar la línea como no editable
            if seccion.es_fija:
                section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
            
            # Añadir productos de la sección que tengan producto seleccionado (automáticamente incluidos)
            productos_incluidos = seccion.line_ids.filtered(lambda l: l.product_id)
            
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
                        'sequence': current_sequence,
                    }
                    
                    product_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create(vals)
                    current_sequence += 10
            else:
                # Si no hay productos, añadir una línea informativa
                SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                    'order_id': order.id,
                    'name': "(Sin productos añadidos en esta sección)",
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'display_type': 'line_note',
                    'sequence': current_sequence,
                })
                current_sequence += 10

        # Nota: No añadimos el capítulo a capitulo_ids para permitir capítulos duplicados
        # La información del capítulo se mantiene en las líneas del pedido
        # order.write({'capitulo_ids': [(4, capitulo.id)]})

        # Añadir condiciones particulares si existen
        if self.condiciones_particulares:
            # Añadir sección de condiciones particulares
            condiciones_section = SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': "=== CONDICIONES PARTICULARES ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'condiciones_particulares': self.condiciones_particulares,  # Guardar en el campo correcto
                'sequence': current_sequence,
            })
            current_sequence += 10

        return {'type': 'ir.actions.act_window_close'}
    

    

    

    
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
        
        # Debug: Mostrar información de validación
        secciones_con_productos = []
        for seccion in self.seccion_ids:
            if seccion.line_ids.filtered(lambda l: l.product_id):
                secciones_con_productos.append(seccion)
        
        _logger.info(f"Validación: {len(secciones_con_productos)} secciones con productos de {len(self.seccion_ids)} total")
        
        # En modo existente, permitir continuar aunque no haya productos añadidos aún
        # ya que el capítulo existente puede tener productos predefinidos
        if self.modo_creacion == 'nuevo' and not secciones_con_productos:
            raise UserError("Debe añadir al menos un producto en alguna sección para crear el presupuesto.")
    
    def add_seccion(self):
        """Añade una nueva sección al wizard"""
        self.ensure_one()
        
        # Calcular la siguiente secuencia
        next_sequence = (max(self.seccion_ids.mapped('sequence')) + 10) if self.seccion_ids else 10
        
        # Crear nueva sección directamente usando write para evitar triggers automáticos
        nueva_seccion_vals = (0, 0, {
            'name': 'Nueva Sección',
            'sequence': next_sequence,
            'es_fija': False,  # Nueva sección no es fija, el usuario puede editarla
            'incluir': False,
        })
        
        # Añadir la nueva sección sin limpiar las existentes
        self.with_context(skip_integrity_check=True).write({
            'seccion_ids': [nueva_seccion_vals]
        })
        
        _logger.info(f"Nueva sección añadida con secuencia {next_sequence}")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def add_another_chapter(self):
        """Añade el capítulo actual y abre el wizard para añadir otro"""
        self.ensure_one()
        
        # Validar datos antes de proceder
        self._validate_wizard_data()
        
        # Ejecutar la lógica de add_to_order sin retornar su resultado
        # Verificar si hay productos para añadir
        # En modo existente, incluir todas las secciones que tengan productos
        # En modo nuevo, solo las secciones marcadas como incluir
        total_productos_a_añadir = 0
        secciones_con_productos = []
        
        if self.modo_creacion == 'existente':
            # En modo existente, incluir todas las secciones que tengan productos
            for seccion in self.seccion_ids:
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        else:
            # En modo nuevo, solo secciones marcadas como incluir
            for seccion in self.seccion_ids.filtered(lambda s: s.incluir):
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        
        if total_productos_a_añadir == 0:
            if self.modo_creacion == 'existente':
                raise UserError(
                    "No hay productos en el capítulo seleccionado para añadir al presupuesto.\n\n"
                    "Para añadir productos:\n"
                    "1. Abra las secciones del capítulo\n"
                    "2. Añada productos usando 'Añadir una línea'\n"
                    "3. Seleccione el producto, cantidad y precio\n"
                    "4. Haga clic en 'Añadir al Presupuesto'"
                )
            else:
                raise UserError(
                    "No hay productos seleccionados para añadir al presupuesto.\n\n"
                    "Para añadir productos:\n"
                    "1. Marque las secciones que desea incluir usando el toggle 'Incluir'\n"
                    "2. Abra cada sección y añada productos usando 'Añadir una línea'\n"
                    "3. Seleccione el producto, cantidad y precio\n"
                    "4. Haga clic en 'Añadir al Presupuesto'"
                )

        # Crear o obtener el capítulo según el modo
        capitulo = self._obtener_o_crear_capitulo()
        
        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # Marcar todas las secciones como fijas después de añadir al pedido
        for seccion in self.seccion_ids:
            seccion.es_fija = True
        
        # Obtener la siguiente secuencia disponible
        max_sequence = max(order.order_line.mapped('sequence')) if order.order_line else 0
        current_sequence = max_sequence + 10
        
        # Añadir título del capítulo como encabezado principal
        nombre_capitulo = capitulo.name if self.modo_creacion == 'existente' else self.nuevo_capitulo_nombre
        SaleOrderLine.with_context(from_capitulo_wizard=True).create({
            'order_id': order.id,
            'name': f"📋 ═══ {nombre_capitulo.upper()} ═══",
            'product_uom_qty': 0,
            'price_unit': 0,
            'display_type': 'line_section',
            'es_encabezado_capitulo': True,
            'sequence': current_sequence,
        })
        current_sequence += 10
        
        # Crear líneas de pedido organizadas por secciones (solo secciones que tienen productos)
        for seccion in secciones_con_productos:
            # Añadir línea de sección como separador
            section_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': f"=== {seccion.name.upper()} ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'sequence': current_sequence,
            })
            current_sequence += 10
            
            # Si la sección es fija, marcar la línea como no editable
            if seccion.es_fija:
                section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
            
            # Añadir productos de la sección que tengan producto seleccionado
            productos_incluidos = seccion.line_ids.filtered(lambda l: l.product_id)
            
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
                        'sequence': current_sequence,
                    }
                    
                    product_line = SaleOrderLine.with_context(from_capitulo_wizard=True).create(vals)
                    current_sequence += 10

        # Nota: No añadimos el capítulo a capitulo_ids para permitir capítulos duplicados
        # La información del capítulo se mantiene en las líneas del pedido
        # order.write({'capitulo_ids': [(4, capitulo.id)]})

        # Añadir condiciones particulares si existen
        if self.condiciones_particulares:
            # Añadir sección de condiciones particulares
            condiciones_section = SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                'order_id': order.id,
                'name': "=== CONDICIONES PARTICULARES ===",
                'product_uom_qty': 0,
                'price_unit': 0,
                'display_type': 'line_section',
                'es_encabezado_seccion': True,
                'condiciones_particulares': self.condiciones_particulares,  # Guardar en el campo correcto
                'sequence': current_sequence,
            })
            current_sequence += 10
        
        # Crear un nuevo wizard para añadir otro capítulo
        # Mantener el capítulo seleccionado para facilitar la adición de duplicados
        new_wizard_vals = {
            'order_id': self.order_id.id,
            'modo_creacion': self.modo_creacion,
        }
        
        # Si estamos en modo existente, mantener el capítulo seleccionado
        if self.modo_creacion == 'existente' and self.capitulo_id:
            new_wizard_vals['capitulo_id'] = self.capitulo_id.id
        elif self.modo_creacion == 'nuevo':
            new_wizard_vals['nuevo_capitulo_nombre'] = self.nuevo_capitulo_nombre
            new_wizard_vals['nuevo_capitulo_descripcion'] = self.nuevo_capitulo_descripcion
        
        new_wizard = self.create(new_wizard_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': new_wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.order_id.id}
        }