# -*- coding: utf-8 -*-
"""
WIZARD DE GESTIÓN DE CAPÍTULOS TÉCNICOS
======================================

Este archivo implementa el wizard (asistente) para la creación y gestión de
capítulos técnicos en presupuestos de venta de Odoo.

FUNCIONALIDAD PRINCIPAL:
- Creación de capítulos nuevos con secciones personalizables
- Utilización de capítulos existentes como plantillas
- Gestión de productos por secciones técnicas
- Configuración de condiciones particulares por capítulo
- Integración directa con presupuestos de venta

MODELOS IMPLEMENTADOS:
1. CapituloWizardSeccion: Secciones dentro del wizard
2. CapituloWizardLine: Líneas de productos dentro de secciones
3. CapituloWizard: Wizard principal de gestión

MODOS DE OPERACIÓN:
- 'existente': Utiliza un capítulo predefinido como base
- 'nuevo': Crea un capítulo completamente nuevo

FLUJO DE TRABAJO:
1. Selección de modo (existente/nuevo)
2. Configuración de secciones y productos
3. Validación de datos
4. Creación de líneas en el presupuesto
5. Estructuración jerárquica del presupuesto

INTEGRACIÓN:
- models/sale_order.py: Destino de las líneas creadas
- models/capitulo.py: Fuente de capítulos existentes
- views/capitulo_wizard_view.xml: Interfaz de usuario
- controllers/main.py: Endpoints para funcionalidad AJAX

REFERENCIAS:
- models/sale_order.py: SaleOrder, SaleOrderLine
- models/capitulo.py: CapituloContrato
- models/capitulo_seccion.py: CapituloSeccion, CapituloSeccionLine
- views/capitulo_wizard_view.xml: Formulario del wizard
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

# Configuración de logging para debugging y monitoreo
_logger = logging.getLogger(__name__)

class CapituloWizardSeccion(models.TransientModel):
    """
    Modelo transitorio para secciones dentro del wizard de capítulos.
    
    Representa una sección técnica (alquiler, montaje, etc.) que puede
    contener múltiples productos y configuraciones específicas.
    
    HERENCIA: models.TransientModel (datos temporales)
    TABLA: capitulo_wizard_seccion (temporal)
    ORDENACIÓN: sequence, name (orden de aparición)
    """
    _name = 'capitulo.wizard.seccion'
    _description = 'Sección del Wizard de Capítulo'
    _order = 'sequence, name'

    # RELACIÓN CON EL WIZARD PRINCIPAL
    wizard_id = fields.Many2one(
        'capitulo.wizard', 
        ondelete='cascade',                     # Eliminar secciones si se elimina wizard
        string='Wizard',
        help='Wizard principal al que pertenece esta sección'
    )
    
    # CONFIGURACIÓN BÁSICA DE LA SECCIÓN
    name = fields.Char(
        string='Nombre de la Sección', 
        required=True, 
        default='Nueva Sección',
        help='Nombre descriptivo de la sección técnica'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición en el presupuesto'
    )
    
    # CONFIGURACIÓN DE COMPORTAMIENTO
    es_fija = fields.Boolean(
        string='Sección Fija', 
        default=False,
        help='Si está marcada, la sección no puede ser modificada por el usuario'
    )
    
    incluir = fields.Boolean(
        string='Incluir en Presupuesto', 
        default=False,
        help='Determina si esta sección se incluirá en el presupuesto final'
    )
    
    # FILTRADO POR CATEGORÍA DE PRODUCTOS
    product_category_id = fields.Many2one(
        'product.category',
        string='Categoría de Productos',
        help='Categoría de productos que se mostrarán en esta sección'
    )
    
    # RELACIÓN CON PRODUCTOS
    line_ids = fields.One2many(
        'capitulo.wizard.line', 
        'seccion_id', 
        string='Productos',
        help='Lista de productos configurados en esta sección'
    )
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe create para asegurar valores por defecto apropiados.
        
        VALIDACIONES:
        - Nombre no vacío (establece 'Nueva Sección' si está vacío)
        - Secuencia por defecto (10 si no se especifica)
        - Estados por defecto para incluir y es_fija
        
        LOGGING:
        - Registra la creación de secciones para debugging
        """
        original_name = vals.get('name')
        _logger.info(f"Creando sección con nombre original: '{original_name}'")
        
        # VALIDACIÓN Y CORRECCIÓN DE NOMBRE
        if not vals.get('name') or vals.get('name').strip() == '':
            vals['name'] = 'Nueva Sección'
            _logger.warning(f"Nombre vacío detectado, estableciendo 'Nueva Sección'. Nombre original: '{original_name}'")
        
        # ESTABLECIMIENTO DE VALORES POR DEFECTO
        if not vals.get('sequence'):
            vals['sequence'] = 10
        if 'incluir' not in vals:
            vals['incluir'] = True
        if 'es_fija' not in vals:
            vals['es_fija'] = False
            
        _logger.info(f"Creando sección final con nombre: '{vals['name']}', es_fija: {vals['es_fija']}")
        return super().create(vals)
    
    def unlink(self):
        """
        Permite la eliminación de secciones en el wizard.
        
        COMPORTAMIENTO:
        - Elimina la sección y todas sus líneas de producto asociadas
        - Utilizado cuando el usuario elimina secciones manualmente
        """
        return super().unlink()
    
    def write(self, vals):
        """
        Permite la modificación de secciones en el wizard.
        
        COMPORTAMIENTO:
        - Actualiza los campos de la sección según los valores proporcionados
        - Mantiene la integridad referencial con las líneas de producto
        """
        return super().write(vals)
    
    @api.constrains('name')
    def _check_name(self):
        """
        Validación de integridad para el nombre de la sección.
        
        VALIDACIONES:
        - El nombre no puede estar vacío
        - El nombre no puede contener solo espacios en blanco
        
        EXCEPCIONES:
        - UserError: Si el nombre no cumple los criterios
        """
        for record in self:
            if not record.name or not record.name.strip():
                raise UserError("El nombre de la sección es obligatorio y no puede estar vacío.")
    
    def unlink_seccion(self):
        """
        Método de conveniencia para eliminar la sección.
        
        PROPÓSITO:
        - Proporciona una interfaz más clara para la eliminación
        - Puede ser llamado desde botones en la vista
        
        RETORNA:
        - Resultado de la operación unlink()
        """
        return self.unlink()
    
    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        """
        Filtra productos cuando cambia la categoría seleccionada.
        
        COMPORTAMIENTO:
        - Limpia los productos previamente seleccionados
        - Actualiza el dominio para mostrar solo productos de la categoría
        - Incluye subcategorías usando 'child_of'
        - Afecta tanto a product_ids como a line_ids.product_id
        
        RETORNA:
        - Diccionario con el nuevo dominio para los campos de productos
        """
        if self.product_category_id:
            # Limpiar productos seleccionados cuando cambie la categoría
            self.product_ids = [(5, 0, 0)]
            _logger.info(f"Categoría seleccionada: {self.product_category_id.name}, "
                        f"Filtrando productos de esta categoría")
            
            domain_filter = [
                ('sale_ok', '=', True), 
                ('categ_id', 'child_of', self.product_category_id.id)
            ]
            
            return {
                'domain': {
                    'product_ids': domain_filter,
                    'line_ids.product_id': domain_filter
                }
            }
        else:
            # Si no hay categoría, mostrar todos los productos vendibles
            domain_filter = [('sale_ok', '=', True)]
            return {
                'domain': {
                    'product_ids': domain_filter,
                    'line_ids.product_id': domain_filter
                }
            }

class CapituloWizardLine(models.TransientModel):
    """
    Modelo transitorio para líneas de productos dentro de secciones del wizard.
    
    Representa un producto específico con su configuración (cantidad, precio, etc.)
    dentro de una sección técnica del wizard.
    
    HERENCIA: models.TransientModel (datos temporales)
    TABLA: capitulo_wizard_line (temporal)
    """
    _name = 'capitulo.wizard.line'
    _description = 'Línea de Configurador de capítulo'

    # RELACIONES JERÁRQUICAS
    wizard_id = fields.Many2one(
        'capitulo.wizard', 
        ondelete='cascade',
        string='Wizard',
        help='Wizard principal (relación indirecta a través de sección)'
    )
    
    seccion_id = fields.Many2one(
        'capitulo.wizard.seccion', 
        string='Sección', 
        ondelete='cascade',
        help='Sección a la que pertenece esta línea de producto'
    )
    
    # CONFIGURACIÓN DEL PRODUCTO
    product_id = fields.Many2one(
        'product.product', 
        string='Producto',
        help='Producto seleccionado para esta línea'
    )
    
    descripcion_personalizada = fields.Char(
        string='Descripción Personalizada',
        help='Descripción alternativa que sobrescribe el nombre del producto'
    )
    
    # CONFIGURACIÓN COMERCIAL
    cantidad = fields.Float(
        string='Cantidad', 
        default=1, 
        required=True,
        help='Cantidad del producto a incluir'
    )
    
    precio_unitario = fields.Float(
        string='Precio', 
        default=0.0,
        help='Precio unitario del producto'
    )
    
    # CONFIGURACIÓN DE COMPORTAMIENTO
    incluir = fields.Boolean(
        string='Incluir', 
        default=False,
        help='Determina si este producto se incluirá en el presupuesto'
    )
    
    es_opcional = fields.Boolean(
        string='Opcional', 
        default=False,
        help='Marca el producto como opcional en el presupuesto'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición dentro de la sección'
    )
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe create para establecer relaciones correctas.
        
        LÓGICA:
        - Establece wizard_id automáticamente desde la sección
        - Registra la creación para debugging
        - Valida la integridad de las relaciones
        
        LOGGING:
        - Información detallada sobre la línea creada
        """
        # ESTABLECIMIENTO AUTOMÁTICO DE WIZARD_ID
        if not vals.get('wizard_id') and vals.get('seccion_id'):
            seccion = self.env['capitulo.wizard.seccion'].browse(vals['seccion_id'])
            if seccion.wizard_id:
                vals['wizard_id'] = seccion.wizard_id.id
                _logger.info(f"Estableciendo wizard_id={vals['wizard_id']} para nueva línea de producto")
        
        line = super().create(vals)
        
        # LOGGING DE CREACIÓN
        _logger.info(f"Línea de producto creada: ID={line.id}, "
                    f"Producto={line.product_id.name if line.product_id else 'Sin producto'}, "
                    f"Sección={line.seccion_id.name if line.seccion_id else 'Sin sección'}")
        return line
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Actualiza automáticamente el precio cuando se selecciona un producto.
        
        COMPORTAMIENTO:
        - Establece precio_unitario desde product.list_price
        - Marca automáticamente como incluido
        - Resetea valores si se deselecciona el producto
        
        LOGGING:
        - Información sobre el producto seleccionado y precio establecido
        """
        if self.product_id:
            # ESTABLECIMIENTO AUTOMÁTICO DE PRECIO
            self.precio_unitario = self.product_id.list_price
            # MARCADO AUTOMÁTICO COMO INCLUIDO
            self.incluir = True
            _logger.info(f"Producto seleccionado: {self.product_id.name}, "
                        f"Precio: {self.precio_unitario}, Auto-incluido: True")
        else:
            # RESETEO DE VALORES
            self.precio_unitario = 0.0
            self.incluir = False

class CapituloWizard(models.TransientModel):
    """
    Wizard principal para la gestión de capítulos técnicos en presupuestos.
    
    Este wizard permite crear capítulos nuevos o utilizar capítulos existentes
    como plantillas, configurando secciones técnicas y productos asociados
    para su posterior inserción en presupuestos de venta.
    
    HERENCIA: models.TransientModel (datos temporales)
    TABLA: capitulo_wizard (temporal)
    
    MODOS DE OPERACIÓN:
    - 'existente': Utiliza un capítulo predefinido como base
    - 'nuevo': Crea un capítulo completamente nuevo
    
    FLUJO DE TRABAJO:
    1. Inicialización con pedido de venta
    2. Selección de modo (existente/nuevo)
    3. Configuración de secciones y productos
    4. Validación de datos
    5. Creación de líneas estructuradas en el presupuesto
    
    FUNCIONALIDADES PRINCIPALES:
    - Gestión de secciones técnicas (alquiler, montaje, portes, etc.)
    - Configuración de productos por sección
    - Validación de integridad de datos
    - Creación automática de estructura jerárquica
    - Soporte para condiciones particulares
    - Capacidad de añadir múltiples capítulos
    
    INTEGRACIÓN:
    - models/sale_order.py: Destino de las líneas creadas
    - models/capitulo.py: Fuente de capítulos existentes
    - views/capitulo_wizard_view.xml: Interfaz de usuario
    """
    _name = 'capitulo.wizard'
    _description = 'Añadir Capítulo'

    # CONFIGURACIÓN DEL MODO DE OPERACIÓN
    modo_creacion = fields.Selection([
        ('existente', 'Usar Capítulo Existente'),
        ('nuevo', 'Crear Nuevo Capítulo')
    ], 
        string='Modo de Creación', 
        default='existente', 
        required=True,
        help='Determina si se utiliza un capítulo existente o se crea uno nuevo'
    )
    
    # CAMPOS PARA CAPÍTULO EXISTENTE
    capitulo_id = fields.Many2one(
        'capitulo.contrato', 
        string='Capítulo',
        help='Capítulo existente a utilizar como plantilla'
    )
    
    # CAMPOS PARA CREAR NUEVO CAPÍTULO
    nuevo_capitulo_nombre = fields.Char(
        string='Nombre del Capítulo',
        help='Nombre del nuevo capítulo a crear'
    )
    
    nuevo_capitulo_descripcion = fields.Text(
        string='Descripción del Capítulo',
        help='Descripción detallada del nuevo capítulo'
    )
    
    # RELACIONES PRINCIPALES
    order_id = fields.Many2one(
        'sale.order', 
        string='Pedido de Venta', 
        required=True,
        help='Presupuesto de venta donde se insertarán las líneas'
    )
    
    seccion_ids = fields.One2many(
        'capitulo.wizard.seccion', 
        'wizard_id', 
        string='Secciones',
        help='Secciones técnicas configuradas en el wizard'
    )
    
    # CONFIGURACIÓN ADICIONAL
    condiciones_particulares = fields.Text(
        string='Condiciones Particulares',
        help='Condiciones específicas que se añadirán al presupuesto'
    )

    @api.model
    def default_get(self, fields):
        """
        Establece valores por defecto al crear el wizard.
        
        COMPORTAMIENTO:
        - Obtiene el pedido de venta desde el contexto
        - Inicializa el wizard con valores apropiados
        - Registra la inicialización para debugging
        
        PARÁMETROS:
        - fields: Lista de campos a inicializar
        
        RETORNA:
        - dict: Valores por defecto establecidos
        
        CONTEXTO ESPERADO:
        - default_order_id: ID del pedido de venta
        - active_id: ID activo (alternativo para order_id)
        """
        res = super().default_get(fields)
        
        # OBTENCIÓN DEL PEDIDO DESDE EL CONTEXTO
        order_id = self.env.context.get('default_order_id') or self.env.context.get('active_id')
        if order_id and 'order_id' in fields:
            res['order_id'] = order_id
        
        _logger.info("default_get: inicializando wizard")
        return res
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe create para inicializar secciones automáticamente.
        
        LÓGICA:
        - Crea el wizard con los valores proporcionados
        - Inicializa secciones predefinidas si es modo nuevo
        - Registra la creación para debugging
        
        PARÁMETROS:
        - vals: Valores para crear el wizard
        
        RETORNA:
        - CapituloWizard: Instancia del wizard creado
        
        SECCIONES PREDEFINIDAS:
        - Alquiler (secuencia 10)
        - Montaje (secuencia 20)
        - Portes (secuencia 30)
        - Otros Conceptos (secuencia 40)
        """
        _logger.info("=== Creando nuevo wizard ===")
        wizard = super().create(vals)
        
        # INICIALIZACIÓN DE SECCIONES PARA MODO NUEVO
        if not wizard.seccion_ids and wizard.modo_creacion == 'nuevo':
            _logger.info("Creando secciones predefinidas para nuevo wizard")
            wizard._crear_secciones_predefinidas()
        
        return wizard
    
    def write(self, vals):
        """
        Sobrescribe write para manejar cambios en el wizard.
        
        COMPORTAMIENTO:
        - Evita recursión infinita con bandera de contexto
        - Permite actualizaciones controladas de campos
        - Mantiene integridad de datos
        
        PARÁMETROS:
        - vals: Valores a actualizar
        
        RETORNA:
        - bool: Resultado de la operación write
        
        CONTEXTO ESPECIAL:
        - skip_integrity_check: Evita validaciones recursivas
        """
        # PREVENCIÓN DE RECURSIÓN INFINITA
        if self.env.context.get('skip_integrity_check'):
            return super().write(vals)
            
        result = super().write(vals)
        return result

    @api.onchange('modo_creacion')
    def onchange_modo_creacion(self):
        """
        Maneja cambios en el modo de creación del wizard.
        
        COMPORTAMIENTO MODO 'existente':
        - Limpia campos de nuevo capítulo
        - Elimina secciones existentes
        - Prepara para selección de capítulo
        
        COMPORTAMIENTO MODO 'nuevo':
        - Limpia selección de capítulo existente
        - Crea secciones predefinidas
        - Prepara para configuración manual
        
        LOGGING:
        - Registra cambios de modo para debugging
        - Información sobre estado de secciones
        """
        _logger.info(f"=== onchange_modo_creacion: {self.modo_creacion} ===")
        
        if self.modo_creacion == 'existente':
            # LIMPIEZA PARA MODO EXISTENTE
            self.nuevo_capitulo_nombre = False
            self.nuevo_capitulo_descripcion = False
            # Limpiar secciones al cambiar a modo existente
            _logger.info("Limpiando secciones para modo existente")
            self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
            
        elif self.modo_creacion == 'nuevo':
            # LIMPIEZA PARA MODO NUEVO
            self.capitulo_id = False
            # Crear secciones predefinidas para modo nuevo
            _logger.info(f"Modo nuevo - Secciones actuales: {len(self.seccion_ids)}")
            self._crear_secciones_predefinidas()
    
    @api.onchange('capitulo_id')
    def onchange_capitulo_id(self):
        """
        Maneja cambios en la selección de capítulo existente.
        
        COMPORTAMIENTO:
        - Solo activo en modo 'existente'
        - Limpia secciones actuales
        - Carga secciones del capítulo seleccionado
        - Carga condiciones particulares
        - Crea secciones predefinidas si el capítulo no tiene secciones
        
        LOGGING:
        - Información sobre capítulo seleccionado
        - Estado de carga de secciones
        """
        if self.modo_creacion != 'existente':
            return
            
        # LIMPIEZA DE ESTADO ANTERIOR
        self.with_context(skip_integrity_check=True, from_onchange=True).write({'seccion_ids': [(5, 0, 0)]})
        self.condiciones_particulares = ''
        
        if not self.capitulo_id:
            return
            
        # CARGA DE CONDICIONES LEGALES
        if self.capitulo_id.condiciones_legales:
            self.condiciones_particulares = self.capitulo_id.condiciones_legales
            
        # CARGA DE SECCIONES DEL CAPÍTULO
        if self.capitulo_id.seccion_ids:
            self._cargar_secciones_existentes()
        else:
            # Si no hay secciones, crear secciones predefinidas
            self._crear_secciones_predefinidas()
    
    def _crear_secciones_predefinidas(self):
        """
        Crea secciones técnicas predefinidas para el wizard.
        
        SECCIONES CREADAS:
        - Alquiler (secuencia 10)
        - Montaje (secuencia 20)
        - Portes (secuencia 30)
        - Otros Conceptos (secuencia 40)
        
        COMPORTAMIENTO:
        - Limpia secciones existentes antes de crear nuevas
        - Establece secciones como fijas en modo existente
        - Registra el proceso para debugging
        - Incluye recuperación de errores
        
        LOGGING:
        - Información detallada del proceso de creación
        - Verificación de secciones creadas
        - Manejo de errores con recuperación automática
        """
        _logger.info("=== Iniciando creación de secciones predefinidas ===")
        
        # DEFINICIÓN DE SECCIONES ESTÁNDAR
        secciones_predefinidas = [
            {'name': 'Alquiler', 'sequence': 10},
            {'name': 'Montaje', 'sequence': 20},
            {'name': 'Portes', 'sequence': 30},
            {'name': 'Otros Conceptos', 'sequence': 40},
        ]
        
        # LIMPIEZA DE SECCIONES EXISTENTES
        _logger.info("Limpiando secciones existentes...")
        self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
        
        # DETERMINACIÓN DE COMPORTAMIENTO SEGÚN MODO
        es_fija = self.modo_creacion == 'existente'
        _logger.info(f"Modo creación: {self.modo_creacion}, es_fija: {es_fija}")
        
        # PREPARACIÓN DE VALORES PARA CREACIÓN
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
        
        # CREACIÓN DE SECCIONES
        _logger.info(f"Creando {len(secciones_vals)} secciones...")
        self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
        
        # VERIFICACIÓN DE CREACIÓN EXITOSA
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
        """
        Método de recuperación para recrear secciones en caso de error.
        
        PROPÓSITO:
        - Proporciona un mecanismo de recuperación robusto
        - Maneja errores en la creación de secciones
        - Crea secciones una por una para mayor control
        
        COMPORTAMIENTO:
        - Limpia completamente las secciones existentes
        - Recrea secciones con manejo individual de errores
        - Registra errores específicos para debugging
        
        LOGGING:
        - Errores específicos por sección
        - Estado final de la recuperación
        """
        try:
            # DEFINICIÓN DE SECCIONES PARA RECUPERACIÓN
            secciones_predefinidas = [
                {'name': 'Alquiler', 'sequence': 10},
                {'name': 'Montaje', 'sequence': 20},
                {'name': 'Portes', 'sequence': 30},
                {'name': 'Otros Conceptos', 'sequence': 40},
            ]
            
            # LIMPIEZA COMPLETA
            self.with_context(skip_integrity_check=True).write({'seccion_ids': [(5, 0, 0)]})
            
            # DETERMINACIÓN DE COMPORTAMIENTO
            es_fija = self.modo_creacion == 'existente'
            
            # PREPARACIÓN CON MANEJO DE ERRORES INDIVIDUAL
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
            
            # CREACIÓN SEGURA
            if secciones_vals:
                self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
                    
        except Exception as e:
            _logger.error(f"Error en recreación segura: {e}")
    
    def _cargar_secciones_existentes(self):
        """
        Carga secciones y productos desde un capítulo existente.
        
        COMPORTAMIENTO:
        - Itera sobre las secciones del capítulo seleccionado
        - Carga productos con sus configuraciones
        - Establece todas las secciones como fijas
        - Marca automáticamente como incluidas
        
        DATOS CARGADOS POR SECCIÓN:
        - Nombre y secuencia
        - Estado fijo (siempre True para existentes)
        - Estado incluido (siempre True para existentes)
        
        DATOS CARGADOS POR PRODUCTO:
        - Producto, descripción personalizada
        - Cantidad y precio unitario
        - Secuencia y estado opcional
        - Estado incluido (siempre True para existentes)
        
        LOGGING:
        - Información sobre secciones y productos cargados
        """
        secciones_vals = []
        for seccion in self.capitulo_id.seccion_ids:
            # CARGA DE PRODUCTOS DE LA SECCIÓN
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
            
            # CONFIGURACIÓN DE LA SECCIÓN
            secciones_vals.append((0, 0, {
                'name': seccion.name,
                'sequence': seccion.sequence,
                'es_fija': True,  # Todas las secciones de capítulos existentes son fijas
                'incluir': True,  # En modo existente, incluir automáticamente todas las secciones
                'line_ids': lineas_vals,
            }))
        
        # CARGA DE SECCIONES CON CONTEXTO SEGURO
        self.with_context(skip_integrity_check=True).write({'seccion_ids': secciones_vals})
    
    def _obtener_o_crear_capitulo(self):
        """
        Obtiene un capítulo existente o crea uno nuevo según el modo.
        
        MODO 'existente':
        - Valida que se haya seleccionado un capítulo
        - Retorna el capítulo seleccionado
        
        MODO 'nuevo':
        - Valida que se haya especificado un nombre
        - Crea un nuevo capítulo con secciones incluidas
        - Establece condiciones particulares
        - Marca como no plantilla
        
        PARÁMETROS:
        - Ninguno (utiliza campos del wizard)
        
        RETORNA:
        - capitulo.contrato: Capítulo existente o recién creado
        
        EXCEPCIONES:
        - UserError: Si faltan datos requeridos
        - UserError: Si el modo no es válido
        
        ESTRUCTURA CREADA (modo nuevo):
        - Capítulo con nombre y descripción
        - Secciones marcadas como incluir
        - Productos con configuraciones completas
        """
        if self.modo_creacion == 'existente':
            # VALIDACIÓN Y RETORNO DE CAPÍTULO EXISTENTE
            if not self.capitulo_id:
                raise UserError("Debe seleccionar un capítulo existente")
            return self.capitulo_id
        
        elif self.modo_creacion == 'nuevo':
            # VALIDACIÓN DE DATOS PARA NUEVO CAPÍTULO
            if not self.nuevo_capitulo_nombre:
                raise UserError("Debe especificar un nombre para el nuevo capítulo")
            
            # CONFIGURACIÓN BÁSICA DEL CAPÍTULO
            capitulo_vals = {
                'name': self.nuevo_capitulo_nombre,
                'description': self.nuevo_capitulo_descripcion,
                'condiciones_legales': self.condiciones_particulares,
                'es_plantilla': False,
            }
            
            # CREACIÓN DE SECCIONES DEL CAPÍTULO
            secciones_vals = []
            for seccion_wizard in self.seccion_ids.filtered(lambda s: s.incluir):
                # Solo incluir secciones marcadas como incluir y que tienen productos
                productos_con_producto = seccion_wizard.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    # CREACIÓN DE LÍNEAS DE PRODUCTO
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
                    
                    # CREACIÓN DE SECCIÓN CON PRODUCTOS
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
        """
        Método principal para añadir el capítulo y sus productos al presupuesto.
        
        FUNCIONALIDAD PRINCIPAL:
        - Valida los datos del wizard antes de proceder
        - Crea o obtiene el capítulo según el modo de operación
        - Genera estructura jerárquica en el presupuesto
        - Añade encabezados de capítulo y sección
        - Inserta líneas de producto con configuraciones
        - Maneja condiciones particulares
        
        ESTRUCTURA CREADA EN EL PRESUPUESTO:
        1. Encabezado principal del capítulo (📋 ═══ NOMBRE ═══)
        2. Encabezados de sección (=== SECCIÓN ===)
        3. Líneas de producto con cantidades y precios
        4. Sección de condiciones particulares (si existen)
        
        COMPORTAMIENTO POR MODO:
        - 'existente': Incluye todas las secciones con productos
        - 'nuevo': Solo secciones marcadas como incluir
        
        VALIDACIONES:
        - Existencia del pedido de venta
        - Datos requeridos según el modo
        - Presencia de productos para añadir
        
        SECUENCIACIÓN:
        - Calcula secuencias automáticamente
        - Mantiene orden jerárquico
        - Incrementos de 10 para permitir inserciones
        
        LOGGING:
        - Información detallada del proceso
        - Estado de secciones y productos
        - Debugging de relaciones
        
        RETORNA:
        - dict: Acción para cerrar el wizard
        
        EXCEPCIONES:
        - UserError: Si no hay pedido de venta
        - UserError: Si no hay productos para añadir
        - UserError: Si faltan datos de validación
        """
        self.ensure_one()
        
        # VALIDACIÓN INICIAL DEL PEDIDO
        if not self.order_id:
            raise UserError("No se encontró el pedido de venta")
        
        # LOGGING DE DEBUGGING DETALLADO
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

        # VALIDACIÓN DE DATOS DEL WIZARD
        self._validate_wizard_data()
        
        # ANÁLISIS DE PRODUCTOS A AÑADIR SEGÚN MODO
        total_productos_a_añadir = 0
        secciones_con_productos = []
        
        if self.modo_creacion == 'existente':
            # MODO EXISTENTE: Incluir todas las secciones con productos
            for seccion in self.seccion_ids:
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        else:
            # MODO NUEVO: Solo secciones marcadas como incluir
            for seccion in self.seccion_ids.filtered(lambda s: s.incluir):
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        
        _logger.info(f"Secciones con productos: {len(secciones_con_productos)}")
        _logger.info(f"Total de productos que se van a añadir: {total_productos_a_añadir}")
        
        # VALIDACIÓN DE PRODUCTOS DISPONIBLES
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

        # OBTENCIÓN O CREACIÓN DEL CAPÍTULO
        capitulo = self._obtener_o_crear_capitulo()
        
        # PREPARACIÓN DE VARIABLES PARA CREACIÓN DE LÍNEAS
        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # MARCADO DE SECCIONES COMO FIJAS DESPUÉS DE AÑADIR
        for seccion in self.seccion_ids:
            seccion.es_fija = True
        
        # CÁLCULO DE SECUENCIA INICIAL
        max_sequence = max(order.order_line.mapped('sequence')) if order.order_line else 0
        current_sequence = max_sequence + 10
        
        # CREACIÓN DEL ENCABEZADO PRINCIPAL DEL CAPÍTULO
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
        
        # CREACIÓN DE ESTRUCTURA POR SECCIONES
        for seccion in secciones_con_productos:
            # CREACIÓN DEL ENCABEZADO DE SECCIÓN
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
            
            # MARCADO VISUAL PARA SECCIONES FIJAS
            if seccion.es_fija:
                section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
            
            # PROCESAMIENTO DE PRODUCTOS DE LA SECCIÓN
            productos_incluidos = seccion.line_ids.filtered(lambda l: l.product_id)
            
            if productos_incluidos:
                # CREACIÓN DE LÍNEAS DE PRODUCTO
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
                # LÍNEA INFORMATIVA PARA SECCIONES SIN PRODUCTOS
                SaleOrderLine.with_context(from_capitulo_wizard=True).create({
                    'order_id': order.id,
                    'name': "(Sin productos añadidos en esta sección)",
                    'product_uom_qty': 0,
                    'price_unit': 0,
                    'display_type': 'line_note',
                    'sequence': current_sequence,
                })
                current_sequence += 10

        # NOTA: Permitir capítulos duplicados sin añadir a capitulo_ids
        # La información del capítulo se mantiene en las líneas del pedido
        # order.write({'capitulo_ids': [(4, capitulo.id)]})

        # PROCESAMIENTO DE CONDICIONES PARTICULARES
        if self.condiciones_particulares:
            # CREACIÓN DE SECCIÓN DE CONDICIONES PARTICULARES
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
        """
        Valida la integridad de los datos del wizard antes de proceder.
        
        VALIDACIONES REALIZADAS:
        - Selección de capítulo en modo 'existente'
        - Nombre especificado en modo 'nuevo'
        - Nombres válidos en todas las secciones
        - Presencia de productos en modo 'nuevo'
        
        COMPORTAMIENTO POR MODO:
        - 'existente': Permite continuar sin productos (pueden estar predefinidos)
        - 'nuevo': Requiere al menos un producto en alguna sección
        
        LOGGING:
        - Información de validación detallada
        - Conteo de secciones con productos
        - Estado general del wizard
        
        EXCEPCIONES:
        - UserError: Si falta selección de capítulo existente
        - UserError: Si falta nombre para nuevo capítulo
        - UserError: Si hay secciones sin nombre válido
        - UserError: Si no hay productos en modo nuevo
        """
        # VALIDACIÓN DE SELECCIÓN EN MODO EXISTENTE
        if self.modo_creacion == 'existente' and not self.capitulo_id:
            raise UserError("Debe seleccionar un capítulo existente.")
        
        # VALIDACIÓN DE NOMBRE EN MODO NUEVO
        if self.modo_creacion == 'nuevo' and not self.nuevo_capitulo_nombre:
            raise UserError("Debe especificar un nombre para el nuevo capítulo.")
        
        # VALIDACIÓN DE NOMBRES DE SECCIONES
        for seccion in self.seccion_ids:
            if not seccion.name or not seccion.name.strip():
                raise UserError(f"La sección en la posición {seccion.sequence} no tiene un nombre válido.")
        
        # ANÁLISIS DE SECCIONES CON PRODUCTOS PARA LOGGING
        secciones_con_productos = []
        for seccion in self.seccion_ids:
            if seccion.line_ids.filtered(lambda l: l.product_id):
                secciones_con_productos.append(seccion)
        
        _logger.info(f"Validación: {len(secciones_con_productos)} secciones con productos de {len(self.seccion_ids)} total")
        
        # VALIDACIÓN ESPECÍFICA PARA MODO NUEVO
        # En modo existente, permitir continuar aunque no haya productos añadidos aún
        # ya que el capítulo existente puede tener productos predefinidos
        if self.modo_creacion == 'nuevo' and not secciones_con_productos:
            raise UserError("Debe añadir al menos un producto en alguna sección para crear el presupuesto.")
    
    def add_seccion(self):
        """
        Añade una nueva sección personalizable al wizard.
        
        FUNCIONALIDAD:
        - Calcula automáticamente la siguiente secuencia disponible
        - Crea una sección editable (no fija)
        - Permite personalización completa por el usuario
        - Mantiene las secciones existentes intactas
        
        CONFIGURACIÓN DE LA NUEVA SECCIÓN:
        - Nombre: 'Nueva Sección' (editable por el usuario)
        - Secuencia: Siguiente disponible (incrementos de 10)
        - Estado fijo: False (completamente editable)
        - Estado incluir: False (usuario debe activar)
        
        COMPORTAMIENTO:
        - No elimina secciones existentes
        - Utiliza contexto seguro para evitar triggers
        - Recarga el wizard para mostrar la nueva sección
        
        LOGGING:
        - Información sobre la secuencia asignada
        
        RETORNA:
        - dict: Acción para recargar el wizard con la nueva sección
        """
        self.ensure_one()
        
        # CÁLCULO DE LA SIGUIENTE SECUENCIA DISPONIBLE
        next_sequence = (max(self.seccion_ids.mapped('sequence')) + 10) if self.seccion_ids else 10
        
        # CONFIGURACIÓN DE LA NUEVA SECCIÓN
        nueva_seccion_vals = (0, 0, {
            'name': 'Nueva Sección',
            'sequence': next_sequence,
            'es_fija': False,  # Nueva sección no es fija, el usuario puede editarla
            'incluir': False,
        })
        
        # CREACIÓN DE LA SECCIÓN SIN AFECTAR LAS EXISTENTES
        self.with_context(skip_integrity_check=True).write({
            'seccion_ids': [nueva_seccion_vals]
        })
        
        _logger.info(f"Nueva sección añadida con secuencia {next_sequence}")
        
        # RECARGA DEL WIZARD PARA MOSTRAR LA NUEVA SECCIÓN
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def add_another_chapter(self):
        """
        Añade el capítulo actual al presupuesto y abre un nuevo wizard.
        
        FLUJO DE TRABAJO:
        1. Valida los datos del wizard actual
        2. Ejecuta toda la lógica de add_to_order
        3. Crea un nuevo wizard para añadir otro capítulo
        4. Mantiene configuraciones útiles del wizard anterior
        
        FUNCIONALIDAD COMPLETA DE ADICIÓN:
        - Análisis de productos según el modo
        - Validación de productos disponibles
        - Creación de estructura jerárquica completa
        - Encabezados de capítulo y sección
        - Líneas de producto con configuraciones
        - Condiciones particulares
        
        CONFIGURACIÓN DEL NUEVO WIZARD:
        - Mantiene el mismo pedido de venta
        - Conserva el modo de creación
        - En modo 'existente': Mantiene el capítulo seleccionado
        - En modo 'nuevo': Mantiene nombre y descripción
        
        VENTAJAS:
        - Permite añadir múltiples capítulos consecutivamente
        - Facilita la duplicación de capítulos
        - Mantiene contexto de trabajo
        - Optimiza el flujo de creación de presupuestos
        
        VALIDACIONES:
        - Todas las validaciones de add_to_order
        - Datos requeridos según el modo
        - Presencia de productos para añadir
        
        LOGGING:
        - Información completa del proceso de adición
        
        RETORNA:
        - dict: Acción para abrir nuevo wizard
        
        EXCEPCIONES:
        - UserError: Si faltan datos de validación
        - UserError: Si no hay productos para añadir
        """
        self.ensure_one()
        
        # VALIDACIÓN INICIAL DE DATOS
        self._validate_wizard_data()
        
        # EJECUCIÓN COMPLETA DE LA LÓGICA DE ADICIÓN
        # Análisis de productos a añadir según modo
        total_productos_a_añadir = 0
        secciones_con_productos = []
        
        if self.modo_creacion == 'existente':
            # MODO EXISTENTE: Incluir todas las secciones con productos
            for seccion in self.seccion_ids:
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        else:
            # MODO NUEVO: Solo secciones marcadas como incluir
            for seccion in self.seccion_ids.filtered(lambda s: s.incluir):
                productos_con_producto = seccion.line_ids.filtered(lambda l: l.product_id)
                if productos_con_producto:
                    total_productos_a_añadir += len(productos_con_producto)
                    secciones_con_productos.append(seccion)
        
        # VALIDACIÓN DE PRODUCTOS DISPONIBLES
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

        # OBTENCIÓN O CREACIÓN DEL CAPÍTULO
        capitulo = self._obtener_o_crear_capitulo()
        
        # PREPARACIÓN PARA CREACIÓN DE LÍNEAS
        order = self.order_id
        SaleOrderLine = self.env['sale.order.line']
        
        # MARCADO DE SECCIONES COMO FIJAS
        for seccion in self.seccion_ids:
            seccion.es_fija = True
        
        # CÁLCULO DE SECUENCIA INICIAL
        max_sequence = max(order.order_line.mapped('sequence')) if order.order_line else 0
        current_sequence = max_sequence + 10
        
        # CREACIÓN DEL ENCABEZADO PRINCIPAL DEL CAPÍTULO
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
        
        # CREACIÓN DE ESTRUCTURA POR SECCIONES
        for seccion in secciones_con_productos:
            # CREACIÓN DEL ENCABEZADO DE SECCIÓN
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
            
            # MARCADO VISUAL PARA SECCIONES FIJAS
            if seccion.es_fija:
                section_line.write({'name': f"🔒 === {seccion.name.upper()} === (SECCIÓN FIJA)"})
            
            # PROCESAMIENTO DE PRODUCTOS DE LA SECCIÓN
            productos_incluidos = seccion.line_ids.filtered(lambda l: l.product_id)
            
            if productos_incluidos:
                # CREACIÓN DE LÍNEAS DE PRODUCTO
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

        # NOTA: Permitir capítulos duplicados sin añadir a capitulo_ids
        # La información del capítulo se mantiene en las líneas del pedido
        # order.write({'capitulo_ids': [(4, capitulo.id)]})

        # PROCESAMIENTO DE CONDICIONES PARTICULARES
        if self.condiciones_particulares:
            # CREACIÓN DE SECCIÓN DE CONDICIONES PARTICULARES
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
        
        # CREACIÓN DEL NUEVO WIZARD PARA AÑADIR OTRO CAPÍTULO
        # Mantener configuraciones útiles del wizard anterior
        new_wizard_vals = {
            'order_id': self.order_id.id,
            'modo_creacion': self.modo_creacion,
        }
        
        # CONSERVACIÓN DE CONFIGURACIONES SEGÚN EL MODO
        if self.modo_creacion == 'existente' and self.capitulo_id:
            # Mantener el capítulo seleccionado para facilitar duplicados
            new_wizard_vals['capitulo_id'] = self.capitulo_id.id
        elif self.modo_creacion == 'nuevo':
            # Mantener nombre y descripción para facilitar variaciones
            new_wizard_vals['nuevo_capitulo_nombre'] = self.nuevo_capitulo_nombre
            new_wizard_vals['nuevo_capitulo_descripcion'] = self.nuevo_capitulo_descripcion
        
        new_wizard = self.create(new_wizard_vals)
        
        # RETORNO DEL NUEVO WIZARD
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.wizard',
            'res_id': new_wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.order_id.id}
        }