# -*- coding: utf-8 -*-
"""
Wizard para Gestión de Capítulos Técnicos
==========================================

Este módulo contiene los wizards (modelos transitorios) para la gestión de capítulos
técnicos en pedidos de venta. Proporciona una interfaz intuitiva para aplicar
capítulos existentes o crear nuevos capítulos con sus secciones y productos.

Modelos incluidos:
- CapituloWizard: Wizard principal para gestión de capítulos
- CapituloWizardSeccion: Modelo transitorio para secciones del wizard
- CapituloWizardLine: Modelo transitorio para líneas de productos

Funcionalidades principales:
- Aplicación de capítulos existentes a pedidos
- Creación de nuevos capítulos desde el wizard
- Configuración de secciones con filtrado por categorías
- Gestión de productos con cantidades y precios personalizables
- Validaciones y controles de integridad

Autor: Sergio
Fecha: 2024
Versión: 1.0
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CapituloWizardSeccion(models.TransientModel):
    """
    Modelo transitorio para las secciones dentro del wizard de capítulos.
    
    Este modelo representa una sección temporal durante la configuración de un capítulo
    en el wizard. Permite al usuario configurar secciones con sus productos antes de
    aplicar el capítulo al pedido de venta.
    
    Características:
    - Modelo transitorio (se elimina automáticamente después del uso)
    - Configuración de categorías para filtrado automático de productos
    - Gestión de secuencias para ordenamiento
    - Validaciones de integridad de datos
    - Soporte para secciones fijas y opcionales
    """
    _name = 'capitulo.wizard.seccion'
    _description = 'Sección del Wizard de Capítulo'
    _order = 'sequence, name'  # Ordenar por secuencia y luego por nombre

    # ========================================
    # CAMPOS DE RELACIÓN Y JERARQUÍA
    # ========================================
    
    wizard_id = fields.Many2one(
        'capitulo.wizard', 
        ondelete='cascade',
        help='Wizard padre al que pertenece esta sección'
    )
    
    # ========================================
    # CAMPOS BÁSICOS DE CONFIGURACIÓN
    # ========================================
    
    name = fields.Char(
        string='Nombre de la Sección', 
        required=True, 
        default='Nueva Sección',
        help='Nombre descriptivo de la sección'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la sección (menor número = mayor prioridad)'
    )
    
    es_fija = fields.Boolean(
        string='Sección Fija', 
        default=False,
        help='Si está marcado, esta sección no se puede modificar en el presupuesto'
    )
    
    incluir = fields.Boolean(
        string='Incluir en Presupuesto', 
        default=False,
        help='Determina si esta sección se incluirá en el presupuesto final'
    )
    
    # ========================================
    # CAMPOS DE FILTRADO Y CATEGORIZACIÓN
    # ========================================
    
    product_category_id = fields.Many2one(
        'product.category', 
        string='Categoría de Productos',
        help='Selecciona una categoría para filtrar automáticamente los productos disponibles. '
             'Solo se mostrarán productos de esta categoría al añadir productos'
    )
    
    # ========================================
    # CAMPOS DE RELACIÓN CON PRODUCTOS
    # ========================================
    
    line_ids = fields.One2many(
        'capitulo.wizard.line', 
        'seccion_id', 
        string='Productos',
        help='Lista de productos configurados en esta sección'
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
    """
    Modelo transitorio para las líneas de productos dentro del wizard de capítulos.
    
    Este modelo representa una línea de producto temporal durante la configuración de un
    capítulo en el wizard. Cada línea contiene información sobre un producto específico,
    su cantidad, precio y configuraciones adicionales.
    
    Características:
    - Modelo transitorio (se elimina automáticamente después del uso)
    - Gestión de productos con cantidades y precios personalizables
    - Soporte para descripciones personalizadas
    - Control de inclusión opcional en el presupuesto
    - Validaciones automáticas de precios y cantidades
    - Secuenciación para ordenamiento personalizado
    """
    _name = 'capitulo.wizard.line'
    _description = 'Línea de Configurador de capítulo'

    # ========================================
    # CAMPOS DE RELACIÓN Y JERARQUÍA
    # ========================================
    
    wizard_id = fields.Many2one(
        'capitulo.wizard', 
        ondelete='cascade',
        help='Wizard padre al que pertenece esta línea'
    )
    
    seccion_id = fields.Many2one(
        'capitulo.wizard.seccion', 
        string='Sección', 
        ondelete='cascade',
        help='Sección a la que pertenece esta línea de producto'
    )
    
    # ========================================
    # CAMPOS DE PRODUCTO Y CONFIGURACIÓN
    # ========================================
    
    product_id = fields.Many2one(
        'product.product', 
        string='Producto',
        help='Producto seleccionado para esta línea'
    )
    
    descripcion_personalizada = fields.Char(
        string='Descripción Personalizada',
        help='Descripción personalizada que sobrescribe la descripción del producto'
    )
    
    # ========================================
    # CAMPOS DE CANTIDAD Y PRECIO
    # ========================================
    
    cantidad = fields.Float(
        string='Cantidad', 
        default=1, 
        required=True,
        help='Cantidad del producto a incluir'
    )
    
    precio_unitario = fields.Float(
        string='Precio', 
        default=0.0,
        help='Precio unitario del producto (se actualiza automáticamente al seleccionar producto)'
    )
    
    # ========================================
    # CAMPOS DE CONTROL Y CONFIGURACIÓN
    # ========================================
    
    incluir = fields.Boolean(
        string='Incluir', 
        default=False,
        help='Determina si esta línea se incluirá en el presupuesto final'
    )
    
    es_opcional = fields.Boolean(
        string='Opcional', 
        default=False,
        help='Marca esta línea como opcional en el presupuesto'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la línea (menor número = mayor prioridad)'
    )
    # ========================================
    # MÉTODOS DE CICLO DE VIDA
    # ========================================
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para asegurar relaciones correctas.
        
        Funcionalidades:
        - Establece automáticamente wizard_id desde la sección padre si no se proporciona
        - Registra la creación de líneas para debugging
        - Valida que las relaciones sean consistentes
        
        Args:
            vals (dict): Valores para crear el registro
            
        Returns:
            CapituloWizardLine: Registro creado
        """
        # Si no se proporciona wizard_id pero sí seccion_id, obtenerlo de la sección
        if not vals.get('wizard_id') and vals.get('seccion_id'):
            seccion = self.env['capitulo.wizard.seccion'].browse(vals['seccion_id'])
            if seccion.wizard_id:
                vals['wizard_id'] = seccion.wizard_id.id
                _logger.info(f"Estableciendo wizard_id={vals['wizard_id']} para nueva línea de producto")
        
        line = super().create(vals)
        _logger.info(f"Línea de producto creada: ID={line.id}, Producto={line.product_id.name if line.product_id else 'Sin producto'}, Sección={line.seccion_id.name if line.seccion_id else 'Sin sección'}")
        return line
    
    # ========================================
    # MÉTODOS DE EVENTOS (ONCHANGE)
    # ========================================
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Actualiza automáticamente los campos relacionados cuando se selecciona un producto.
        
        Funcionalidades:
        - Establece el precio unitario desde el precio de lista del producto
        - Marca automáticamente la línea como incluida
        - Resetea valores cuando se deselecciona el producto
        - Registra los cambios para debugging
        
        Triggered by: Cambio en el campo product_id
        """
        if self.product_id:
            self.precio_unitario = self.product_id.list_price
            # Automáticamente marcar como incluido (aunque no sea visible en la interfaz)
            self.incluir = True
            _logger.info(f"Producto seleccionado: {self.product_id.name}, Precio: {self.precio_unitario}, Auto-incluido: True")
        else:
            self.precio_unitario = 0.0
            self.incluir = False

class CapituloWizard(models.TransientModel):
    """
    Wizard principal para la gestión de capítulos técnicos en pedidos de venta.
    
    Este wizard permite a los usuarios aplicar capítulos existentes o crear nuevos
    capítulos con sus secciones y productos asociados. Proporciona una interfaz
    intuitiva para configurar todos los aspectos de un capítulo antes de aplicarlo
    al pedido de venta.
    
    Características principales:
    - Dos modos de operación: usar capítulo existente o crear nuevo
    - Gestión dinámica de secciones con productos
    - Validaciones automáticas de integridad
    - Soporte para plantillas y herencia
    - Interfaz responsive con actualizaciones en tiempo real
    - Logging detallado para debugging y auditoría
    
    Flujo de trabajo:
    1. Selección del modo de creación (existente/nuevo)
    2. Configuración de secciones y productos
    3. Validación de datos
    4. Aplicación al pedido de venta
    """
    _name = 'capitulo.wizard'
    _description = 'Añadir Capítulo'

    # ========================================
    # CAMPOS DE CONFIGURACIÓN PRINCIPAL
    # ========================================
    
    # Modo de operación
    modo_creacion = fields.Selection([
        ('existente', 'Usar Capítulo Existente'),
        ('nuevo', 'Crear Nuevo Capítulo')
    ], string='Modo de Creación', default='existente', required=True,
       help='Determina si se usará un capítulo existente o se creará uno nuevo')
    
    # ========================================
    # CAMPOS PARA CAPÍTULO EXISTENTE
    # ========================================
    
    # Campos para capítulo existente
    capitulo_id = fields.Many2one(
        'capitulo.contrato', 
        string='Capítulo',
        help='Capítulo existente a aplicar al pedido'
    )
    
    # ========================================
    # CAMPOS PARA NUEVO CAPÍTULO
    # ========================================
    
    # Campos para crear nuevo capítulo
    nuevo_capitulo_nombre = fields.Char(
        string='Nombre del Capítulo',
        help='Nombre para el nuevo capítulo a crear'
    )
    
    nuevo_capitulo_descripcion = fields.Text(
        string='Descripción del Capítulo',
        help='Descripción detallada del nuevo capítulo'
    )
    
    # ========================================
    # CAMPOS DE RELACIÓN Y DATOS
    # ========================================
    
    order_id = fields.Many2one(
        'sale.order', 
        string='Pedido de Venta', 
        required=True,
        help='Pedido de venta al que se aplicará el capítulo'
    )
    
    seccion_ids = fields.One2many(
        'capitulo.wizard.seccion', 
        'wizard_id', 
        string='Secciones',
        help='Secciones configuradas en este wizard'
    )
    
    condiciones_particulares = fields.Text(
        string='Condiciones Particulares',
        help='Condiciones específicas para este capítulo'
    )

    # ========================================
    # MÉTODOS DE INICIALIZACIÓN Y CICLO DE VIDA
    # ========================================

    @api.model
    def default_get(self, fields):
        """
        Establece valores por defecto al crear el wizard.
        
        Funcionalidades:
        - Obtiene el pedido de venta desde el contexto
        - Inicializa el wizard con valores apropiados
        - Registra la inicialización para debugging
        
        Args:
            fields (list): Lista de campos a inicializar
            
        Returns:
            dict: Valores por defecto para los campos
        """
        res = super().default_get(fields)
        # Obtener el pedido desde el contexto
        order_id = self.env.context.get('default_order_id') or self.env.context.get('active_id')
        if order_id and 'order_id' in fields:
            res['order_id'] = order_id
        
        _logger.info("default_get: inicializando wizard")
        return res
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para inicialización personalizada.
        
        Funcionalidades:
        - Crea secciones predefinidas para modo nuevo
        - Valida la configuración inicial
        - Registra la creación del wizard
        
        Args:
            vals (dict): Valores para crear el wizard
            
        Returns:
            CapituloWizard: Wizard creado
        """
        _logger.info("=== Creando nuevo wizard ===")
        wizard = super().create(vals)
        
        # Si no hay secciones y estamos en modo nuevo, crear secciones predefinidas
        if not wizard.seccion_ids and wizard.modo_creacion == 'nuevo':
            _logger.info("Creando secciones predefinidas para nuevo wizard")
            wizard._crear_secciones_predefinidas()
        
        return wizard
    
    def write(self, vals):
        """
        Sobrescribe el método write para manejar actualizaciones.
        
        Funcionalidades:
        - Evita recursión infinita con banderas de contexto
        - Mantiene la integridad de los datos
        - Permite actualizaciones controladas
        
        Args:
            vals (dict): Valores a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        # Evitar recursión infinita con una bandera de contexto
        if self.env.context.get('skip_integrity_check'):
            return super().write(vals)
            
        result = super().write(vals)
        return result

    # ========================================
    # MÉTODOS DE EVENTOS (ONCHANGE)
    # ========================================

    @api.onchange('modo_creacion')
    def onchange_modo_creacion(self):
        """
        Maneja el cambio de modo de creación del wizard.
        
        Funcionalidades:
        - Limpia campos específicos según el modo seleccionado
        - Crea secciones predefinidas para modo nuevo
        - Evita conflictos entre modos de operación
        - Registra los cambios para debugging
        
        Triggered by: Cambio en el campo modo_creacion
        """
        _logger.info(f"=== onchange_modo_creacion: {self.modo_creacion} ===")
        
        if self.modo_creacion == 'existente':
            self.nuevo_capitulo_nombre = False
            self.nuevo_capitulo_descripcion = False
            # Limpiar secciones al cambiar a modo existente usando contexto para evitar recursión
            _logger.info("Limpiando secciones para modo existente")
            self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
        elif self.modo_creacion == 'nuevo':
            self.capitulo_id = False
            # Crear secciones predefinidas para modo nuevo
            _logger.info(f"Modo nuevo - Secciones actuales: {len(self.seccion_ids)}")
            self._crear_secciones_predefinidas()
    
    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """
        Maneja la selección de un capítulo existente.
        
        Funcionalidades:
        - Carga las secciones del capítulo seleccionado
        - Establece las condiciones legales
        - Crea secciones predefinidas si no existen
        - Valida que el modo sea correcto
        
        Triggered by: Cambio en el campo capitulo_id
        """
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
        else:
            # Si no hay secciones, crear secciones predefinidas
            self._crear_secciones_predefinidas()
    

    

    

    

    

    
    def _crear_secciones_predefinidas(self):
        """Crea secciones predefinidas básicas"""
        _logger.info("=== Iniciando creación de secciones predefinidas ===")
        
        secciones_predefinidas = [
            {'name': 'Alquiler', 'sequence': 10},
            {'name': 'Montaje', 'sequence': 20},
            {'name': 'Portes', 'sequence': 30},
            {'name': 'Otros Conceptos', 'sequence': 40},
        ]
        
        # Limpiar secciones existentes primero usando contexto para evitar recursión
        _logger.info("Limpiando secciones existentes...")
        self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
        
        # Determinar si las secciones deben ser fijas según el modo
        es_fija = self.modo_creacion == 'existente'
        _logger.info(f"Modo creación: {self.modo_creacion}, es_fija: {es_fija}")
        
        secciones_vals = []
        for seccion_data in secciones_predefinidas:
            vals = {
                'wizard_id': self.id,  # Asegurar la relación
                'name': seccion_data['name'],
                'sequence': seccion_data['sequence'],
                'es_fija': es_fija,  # Fijas solo en modo existente
                'incluir': False,  # Por defecto no incluir, el usuario debe seleccionar
                'line_ids': [],
            }
            secciones_vals.append((0, 0, vals))
            _logger.info(f"Preparando sección: {seccion_data['name']} con wizard_id={self.id}")
        
        # Crear secciones usando contexto para evitar recursión
        _logger.info(f"Creando {len(secciones_vals)} secciones...")
        self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
        
        # Verificar que se crearon correctamente
        try:
            # Forzar flush para asegurar que los datos se escriban
            self.env.flush_all()
            _logger.info(f"Secciones creadas exitosamente. Total: {len(self.seccion_ids)}")
            
            # Verificar nombres
            for seccion in self.seccion_ids:
                _logger.info(f"Sección creada: ID={seccion.id}, Nombre='{seccion.name}', Fija={seccion.es_fija}")
                
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
                        'incluir': False,  # Por defecto no incluir, el usuario debe seleccionar
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