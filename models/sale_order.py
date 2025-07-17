# -*- coding: utf-8 -*-
"""
Módulo: sale_order.py
===================

FUNCIONALIDAD PRINCIPAL:
- Extensión del modelo sale.order para integrar el sistema de capítulos técnicos
- Gestión de presupuestos estructurados con capítulos y secciones jerárquicas
- Widget acordeón para visualización interactiva de la estructura
- Operaciones CRUD para productos dentro de secciones específicas
- Sistema de validaciones para mantener la integridad estructural

ARQUITECTURA DE DATOS:
- Hereda de sale.order añadiendo campos específicos para capítulos
- Extiende sale.order.line con campos de control estructural
- Integración con modelos capitulo.py y capitulo_seccion.py
- Comunicación bidireccional con JavaScript mediante controladores

FUNCIONALIDADES CLAVE:
1. Agrupación automática de líneas por capítulos y secciones
2. Widget acordeón para navegación visual de la estructura
3. Inserción controlada de productos en secciones específicas
4. Validaciones de integridad para encabezados estructurales
5. Sistema de logging extensivo para depuración
6. Gestión de condiciones particulares por sección

COMUNICACIÓN CON FRONTEND:
- Método add_product_to_section: Endpoint para añadir productos vía JavaScript
- Campo capitulos_agrupados: JSON para renderizado del widget acordeón
- Método save_condiciones_particulares: Persistencia de texto libre

REFERENCIAS PRINCIPALES:
- models/capitulo.py: Definición de capítulos y plantillas
- models/capitulo_seccion.py: Estructura de secciones y líneas
- controllers/main.py: Endpoints HTTP para comunicación
- static/src/js/capitulos_accordion_widget.js: Widget frontend
- wizard/capitulo_wizard.py: Interface de gestión de capítulos
- views/sale_order_view.xml: Vistas con widget acordeón integrado

MÉTODOS PRINCIPALES:
- _compute_capitulos_agrupados(): Agrupa líneas en estructura JSON
- _compute_tiene_multiples_capitulos(): Determina visibilidad del acordeón
- add_product_to_section(): Inserta productos en secciones específicas
- save_condiciones_particulares(): Guarda texto libre por sección
- action_open_capitulo_wizard(): Abre wizard de gestión
- toggle_capitulo_collapsed(): Controla estado de expansión

VALIDACIONES Y SEGURIDAD:
- Prevención de eliminación de encabezados estructurales
- Control de modificación de campos críticos
- Validación de permisos en operaciones CRUD
- Logging extensivo para auditoría y depuración
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    """
    Extensión del modelo sale.order para integrar capítulos técnicos estructurados.
    
    HERENCIA: sale.order
    FUNCIONALIDAD: Gestión de presupuestos con estructura jerárquica de capítulos y secciones
    
    CAMPOS AÑADIDOS:
    - capitulo_ids: Relación Many2many con capítulos aplicados al presupuesto
    - capitulos_agrupados: JSON computed con estructura para widget acordeón
    - tiene_multiples_capitulos: Boolean computed para mostrar/ocultar acordeón
    
    MÉTODOS PRINCIPALES:
    - _compute_capitulos_agrupados(): Genera estructura JSON para frontend
    - add_product_to_section(): Inserta productos en secciones específicas
    - action_open_capitulo_wizard(): Abre interface de gestión de capítulos
    
    INTEGRACIÓN:
    - Frontend: Widget acordeón JavaScript para navegación visual
    - Backend: Controladores HTTP para operaciones CRUD
    - Modelos: Capítulos, secciones y líneas de producto
    """
    _inherit = 'sale.order'
    
    # Relación Many2many con los capítulos aplicados a este presupuesto
    capitulo_ids = fields.Many2many(
        'capitulo.contrato',
        string='Capítulos',
        help="Capítulos técnicos aplicados a este presupuesto"
    )
    
    # Campo computed que contiene la estructura JSON para el widget acordeón
    capitulos_agrupados = fields.Text(
        string='Capítulos Agrupados',
        compute='_compute_capitulos_agrupados',
        store=False,
        help="Estructura JSON con capítulos y secciones para el widget acordeón"
    )
    
    # Campo computed que determina si mostrar el widget acordeón
    tiene_multiples_capitulos = fields.Boolean(
        string='Tiene Múltiples Capítulos',
        compute='_compute_tiene_multiples_capitulos',
        store=False,
        help="Indica si el presupuesto tiene estructura de capítulos para mostrar el acordeón"
    )

    def _get_base_name(self, decorated_name):
        """Extrae el nombre base de un capítulo o sección decorado."""
        import re
        name = str(decorated_name)
        # 1. Eliminar sufijos como (SECCIÓN FIJA) o contadores
        name = re.sub(r'\s*\((SECCIÓN FIJA|\d+)\)$', '', name).strip()
        # 2. Eliminar caracteres decorativos de los extremos
        decorative_chars = ' \t\n\r=═🔒📋'
        name = name.strip(decorative_chars)
        return name
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo', 'order_line.es_encabezado_seccion', 'order_line.sequence')
    def _compute_capitulos_agrupados(self):
        """
        Calcula la estructura JSON de capítulos y secciones para el widget acordeón.
        
        PROPÓSITO:
        - Agrupa las líneas del pedido en una estructura jerárquica
        - Genera JSON compatible con el widget acordeón JavaScript
        - Mantiene el orden secuencial de capítulos, secciones y productos
        
        LÓGICA DE AGRUPACIÓN:
        1. Recorre todas las líneas ordenadas por secuencia
        2. Identifica encabezados de capítulos y secciones
        3. Agrupa productos bajo su sección correspondiente
        4. Calcula subtotales por sección y capítulo
        
        ESTRUCTURA JSON GENERADA:
        {
            "capitulos": [
                {
                    "nombre": "Capítulo 1",
                    "collapsed": false,
                    "subtotal": 1500.00,
                    "secciones": [
                        {
                            "nombre": "Sección A",
                            "productos": [
                                {
                                    "id": 123,
                                    "nombre": "Producto X",
                                    "cantidad": 2,
                                    "precio": 100.00,
                                    "subtotal": 200.00
                                }
                            ],
                            "subtotal": 200.00,
                            "condiciones_particulares": "Texto libre..."
                        }
                    ]
                }
            ]
        }
        
        DEPENDENCIAS:
        - order_line: Líneas del pedido
        - es_encabezado_capitulo: Flag de encabezado de capítulo
        - es_encabezado_seccion: Flag de encabezado de sección
        - sequence: Orden secuencial de las líneas
        
        REFERENCIAS:
        - static/src/js/capitulos_accordion_widget.js: Consume este JSON
        - views/sale_order_view.xml: Widget que renderiza la estructura
        """
        for order in self:
            # Inicializar estructura de datos
            capitulos_data = {
                'capitulos': []
            }
            
            # Variables de control para el procesamiento secuencial
            capitulo_actual = None
            seccion_actual = None
            
            # Procesar todas las líneas ordenadas por secuencia
            for line in order.order_line.sorted('sequence'):
                if line.es_encabezado_capitulo:
                    # Nuevo capítulo encontrado
                    capitulo_actual = {
                        'nombre': line.name,
                        'collapsed': getattr(line, 'collapsed', False),  # Estado de expansión
                        'subtotal': 0.0,
                        'secciones': []
                    }
                    capitulos_data['capitulos'].append(capitulo_actual)
                    seccion_actual = None  # Reset sección al cambiar de capítulo
                    
                elif line.es_encabezado_seccion and capitulo_actual:
                    # Nueva sección encontrada dentro del capítulo actual
                    seccion_actual = {
                        'nombre': line.name,
                        'productos': [],
                        'subtotal': 0.0,
                        'condiciones_particulares': getattr(line, 'condiciones_particulares', '') or ''
                    }
                    capitulo_actual['secciones'].append(seccion_actual)
                    
                elif seccion_actual and not line.es_encabezado_capitulo and not line.es_encabezado_seccion:
                    # Producto normal dentro de una sección
                    producto_data = {
                        'id': line.id,
                        'nombre': line.name,
                        'cantidad': line.product_uom_qty,
                        'precio': line.price_unit,
                        'subtotal': line.price_subtotal
                    }
                    seccion_actual['productos'].append(producto_data)
                    
                    # Acumular subtotales
                    seccion_actual['subtotal'] += line.price_subtotal
                    capitulo_actual['subtotal'] += line.price_subtotal
            
            # Convertir a JSON para el frontend
            order.capitulos_agrupados = json.dumps(capitulos_data, ensure_ascii=False)
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo')
    def _compute_tiene_multiples_capitulos(self):
        """
        Determina si el presupuesto tiene estructura de capítulos para mostrar el widget acordeón.
        
        PROPÓSITO:
        - Controla la visibilidad del widget acordeón en la vista
        - Optimiza el renderizado mostrando el acordeón solo cuando es necesario
        - Evita mostrar el widget en presupuestos sin estructura de capítulos
        
        LÓGICA:
        - Cuenta las líneas marcadas como encabezados de capítulo
        - Si hay al menos un encabezado de capítulo, activa el acordeón
        - El acordeón se muestra incluso con un solo capítulo para consistencia
        
        DEPENDENCIAS:
        - order_line: Líneas del pedido
        - es_encabezado_capitulo: Flag que identifica encabezados de capítulo
        
        REFERENCIAS:
        - views/sale_order_view.xml: Usa este campo para mostrar/ocultar el widget
        - static/src/js/capitulos_accordion_widget.js: Widget que se controla
        """
        for order in self:
            # Contar encabezados de capítulo en las líneas del pedido
            capitulos_count = len(order.order_line.filtered('es_encabezado_capitulo'))
            # Activar acordeón si hay al menos un capítulo estructurado
            order.tiene_multiples_capitulos = capitulos_count >= 1
    
    def action_add_capitulo(self):
        """
        Abre el wizard de gestión de capítulos para este presupuesto.
        
        PROPÓSITO:
        - Proporciona interface gráfica para gestionar capítulos y secciones
        - Permite añadir, modificar y eliminar estructura de capítulos
        - Facilita la aplicación de plantillas predefinidas
        
        FUNCIONALIDAD:
        - Crea una acción de ventana para abrir el wizard
        - Pasa el ID del presupuesto actual como contexto
        - Configura la vista como modal para mejor UX
        
        RETORNO:
        - Dict con configuración de acción de ventana de Odoo
        - Incluye vista, modelo objetivo, contexto y configuración modal
        
        REFERENCIAS:
        - wizard/capitulo_wizard.py: Wizard que se abre
        - views/capitulo_wizard_view.xml: Vista del wizard
        - views/sale_order_view.xml: Botón que llama a este método
        """
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
        """
        Alterna el estado de expansión/colapso de un capítulo en el acordeón.
        
        PROPÓSITO:
        - Controla la visibilidad de secciones dentro de cada capítulo
        - Mejora la experiencia de usuario permitiendo navegación selectiva
        - Mantiene el estado de expansión para cada capítulo individualmente
        
        PARÁMETROS:
        - capitulo_index (int): Índice del capítulo en la estructura JSON
        
        LÓGICA:
        1. Parsea la estructura JSON de capítulos agrupados
        2. Alterna el campo 'collapsed' del capítulo especificado
        3. Actualiza la estructura JSON con el nuevo estado
        4. Retorna acción de recarga para actualizar la vista
        
        RETORNO:
        - Dict con acción de cliente para recargar la vista
        
        REFERENCIAS:
        - static/src/js/capitulos_accordion_widget.js: Llama a este método
        - controllers/main.py: Podría exponer este método vía HTTP
        """
        import json
        
        self.ensure_one()
        capitulos = json.loads(self.capitulos_agrupados or '[]')
        
        if 0 <= capitulo_index < len(capitulos):
            capitulos[capitulo_index]['collapsed'] = not capitulos[capitulo_index].get('collapsed', True)
            self.capitulos_agrupados = json.dumps(capitulos)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    @api.model
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """
        Añade un producto a una sección específica de un capítulo en el presupuesto.
        
        PROPÓSITO:
        - Insertar productos en secciones específicas manteniendo la estructura jerárquica
        - Validar la integridad de la estructura de capítulos y secciones
        - Controlar el orden secuencial de las líneas del presupuesto
        - Proporcionar logging extensivo para depuración y auditoría
        
        PARÁMETROS:
        - order_id (int): ID del presupuesto donde insertar el producto
        - capitulo_name (str): Nombre del capítulo objetivo
        - seccion_name (str): Nombre de la sección objetivo
        - product_id (int): ID del producto a insertar
        - quantity (float): Cantidad del producto (default: 1.0)
        
        LÓGICA DE INSERCIÓN:
        1. Validación de parámetros de entrada
        2. Búsqueda y validación del presupuesto
        3. Localización del capítulo en la estructura
        4. Localización de la sección dentro del capítulo
        5. Validación de tipo de sección (no permitir en secciones de solo texto)
        6. Cálculo de posición de inserción (inmediatamente después del encabezado)
        7. Desplazamiento de líneas existentes para hacer espacio
        8. Creación de la nueva línea de producto
        9. Recálculo de estructura JSON para el frontend
        
        VALIDACIONES:
        - Existencia del presupuesto y permisos de acceso
        - Existencia del producto en el catálogo
        - Existencia del capítulo en el presupuesto
        - Existencia de la sección en el capítulo
        - Tipo de sección (no permitir productos en "condiciones particulares")
        
        MANEJO DE SECUENCIAS:
        - Inserta inmediatamente después del encabezado de sección
        - Desplaza todas las líneas posteriores +1 en secuencia
        - Mantiene el orden jerárquico: capítulo → sección → productos
        
        LOGGING Y DEPURACIÓN:
        - Log detallado de cada paso del proceso
        - Información de validaciones y errores
        - Estado de secuencias antes y después de la inserción
        - Confirmación de creación exitosa
        
        RETORNO:
        - Dict con resultado de la operación:
          {
              'success': True/False,
              'message': 'Descripción del resultado',
              'line_id': ID de la línea creada (si exitoso)
          }
        
        EXCEPCIONES:
        - UserError: Para errores de validación y lógica de negocio
        - Exception: Para errores técnicos durante la creación
        
        REFERENCIAS:
        - controllers/main.py: Expone este método vía HTTP/JSON
        - static/src/js/capitulos_accordion_widget.js: Llama a este método
        - models/sale_order.py (SaleOrderLine): Modelo de líneas modificado
        - wizard/capitulo_wizard.py: Usa funcionalidad similar
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # === VALIDACIÓN DE PARÁMETROS ===
        _logger.info(f"DEBUG ADD_PRODUCT: Iniciando inserción de producto")
        _logger.info(f"DEBUG ADD_PRODUCT: - Order ID: {order_id}")
        _logger.info(f"DEBUG ADD_PRODUCT: - Capítulo: '{capitulo_name}'")
        _logger.info(f"DEBUG ADD_PRODUCT: - Sección: '{seccion_name}'")
        _logger.info(f"DEBUG ADD_PRODUCT: - Product ID: {product_id}")
        _logger.info(f"DEBUG ADD_PRODUCT: - Cantidad: {quantity}")
        
        if not all([order_id, capitulo_name, seccion_name, product_id]):
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ Parámetros faltantes")
            raise UserError("Faltan parámetros requeridos para añadir el producto")
        
        # === VALIDACIÓN DEL PRESUPUESTO ===
        try:
            order = self.browse(order_id)
            order.ensure_one()
            _logger.info(f"DEBUG ADD_PRODUCT: ✅ Presupuesto encontrado: {order.name}")
        except Exception as e:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ Error al acceder al presupuesto: {str(e)}")
            raise UserError(f"No se pudo acceder al presupuesto: {str(e)}")
        
        # === VALIDACIÓN DEL PRODUCTO ===
        try:
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                _logger.error(f"DEBUG ADD_PRODUCT: ❌ Producto {product_id} no existe")
                raise UserError("El producto seleccionado no existe")
                
            _logger.info(f"DEBUG ADD_PRODUCT: ✅ Producto encontrado: {product.name} (ID: {product.id})")
        except Exception as e:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ Error al validar producto: {str(e)}")
            raise e
        
        _logger.info(f"DEBUG ADD_PRODUCT: Producto encontrado: {product.name}")
        
        # === BÚSQUEDA DEL CAPÍTULO ===
        capitulo_line = None
        seccion_line = None
        
        _logger.info(f"DEBUG ADD_PRODUCT: Buscando capítulo '{capitulo_name}' y sección '{seccion_name}'")
        _logger.info(f"DEBUG ADD_PRODUCT: Líneas en el pedido:")
        for line in order.order_line.sorted('sequence'):
            _logger.info(f"DEBUG ADD_PRODUCT: - Línea {line.sequence}: '{line.name}' (Capítulo: {line.es_encabezado_capitulo}, Sección: {line.es_encabezado_seccion})")
        
        # Buscar el encabezado del capítulo
        for line in order.order_line.sorted('sequence'):
            if line.es_encabezado_capitulo:
                line_base_name = self._get_base_name(line.name)
                capitulo_base_name = self._get_base_name(capitulo_name)
                
                _logger.info(f"DEBUG ADD_PRODUCT: Comparando capítulo base '{line_base_name}' con '{capitulo_base_name}'")
                
                if line_base_name.upper() == capitulo_base_name.upper():
                    capitulo_line = line
                    _logger.info(f"DEBUG ADD_PRODUCT: ✅ Capítulo encontrado: {line.name}")
                    break
        
        if not capitulo_line:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ No se encontró el capítulo '{capitulo_name}'")
            raise UserError(f"No se encontró el capítulo: {capitulo_name}")
        
        # === BÚSQUEDA DE LA SECCIÓN ===
        _logger.info(f"DEBUG ADD_PRODUCT: Buscando sección '{seccion_name}' después del capítulo '{capitulo_line.name}'")
        _logger.info(f"DEBUG ADD_PRODUCT: Capítulo encontrado en secuencia: {capitulo_line.sequence}")
        
        # Obtener todas las líneas después del capítulo
        # Si todas las líneas tienen la misma secuencia, usar el ID para ordenar
        all_lines = order.order_line.sorted(lambda l: (l.sequence, l.id))
        capitulo_index = None
        for i, line in enumerate(all_lines):
            if line.id == capitulo_line.id:
                capitulo_index = i
                break
        
        if capitulo_index is not None:
            lines_after_chapter = all_lines[capitulo_index + 1:]
        else:
            lines_after_chapter = order.order_line.filtered(lambda l: l.sequence > capitulo_line.sequence).sorted('sequence')
        
        _logger.info(f"DEBUG ADD_PRODUCT: Líneas después del capítulo: {len(lines_after_chapter)}")
        
        # Buscar la sección específica dentro del capítulo
        for line in lines_after_chapter:
            _logger.info(f"DEBUG ADD_PRODUCT: Revisando línea {line.sequence}: '{line.name}' (Capítulo: {line.es_encabezado_capitulo}, Sección: {line.es_encabezado_seccion})")
            
            if line.es_encabezado_capitulo:
                # Si encontramos otro capítulo, paramos la búsqueda
                _logger.info(f"DEBUG ADD_PRODUCT: Encontrado otro capítulo, parando búsqueda")
                break
            elif line.es_encabezado_seccion:
                line_base_name = self._get_base_name(line.name)
                seccion_base_name = self._get_base_name(seccion_name)
                
                _logger.info(f"DEBUG ADD_PRODUCT: Comparando sección base '{line_base_name}' con '{seccion_base_name}'")
                
                if line_base_name.upper() == seccion_base_name.upper():
                    seccion_line = line
                    _logger.info(f"DEBUG ADD_PRODUCT: ✅ Sección encontrada: {line.name}")
                    break
            else:
                _logger.info(f"DEBUG ADD_PRODUCT: Línea de producto: '{line.name}' (secuencia: {line.sequence})")
        
        if not seccion_line:
            raise UserError(f"No se encontró la sección: {seccion_name} en el capítulo: {capitulo_name}")
        
        # === VALIDACIÓN DE TIPO DE SECCIÓN ===
        seccion_name_lower = seccion_name.lower().strip()
        if 'condiciones particulares' in seccion_name_lower:
            _logger.warning(f"DEBUG ADD_PRODUCT: ❌ Intento de añadir producto a sección de solo texto: '{seccion_name}'")
            raise UserError(f"No se pueden añadir productos a la sección '{seccion_name}'. Esta sección es solo para texto editable.")
        
        # === CÁLCULO DE POSICIÓN DE INSERCIÓN ===
        # Estrategia: insertar inmediatamente después del encabezado de sección
        insert_sequence = seccion_line.sequence + 1
        _logger.info(f"DEBUG: Insertando producto inmediatamente después de la sección '{seccion_line.name}' (seq: {seccion_line.sequence})")
        _logger.info(f"DEBUG: Secuencia de inserción: {insert_sequence}")

        # === DESPLAZAMIENTO DE LÍNEAS EXISTENTES ===
        # Desplazar todas las líneas que tengan secuencia >= insert_sequence
        lines_to_shift = order.order_line.filtered(lambda l: l.sequence >= insert_sequence)
        _logger.info(f"DEBUG: {len(lines_to_shift)} líneas para desplazar.")

        # Ordenamos de forma descendente para evitar conflictos de clave única al actualizar
        for line_to_shift in lines_to_shift.sorted(key=lambda r: r.sequence, reverse=True):
            new_seq = line_to_shift.sequence + 1
            _logger.info(f"DEBUG: Desplazando línea '{line_to_shift.name}' de {line_to_shift.sequence} a {new_seq}.")
            # Usamos el contexto para saltar la validación de escritura en encabezados
            line_to_shift.with_context(from_capitulo_wizard=True).sequence = new_seq
        
        _logger.info(f"DEBUG: Secuencia de inserción final: {insert_sequence}")
        
        # === CREACIÓN DE LA NUEVA LÍNEA ===
        try:
            new_line_vals = {
                'order_id': order.id,
                'product_id': product.id,
                'name': product.name,
                'product_uom_qty': quantity,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
                'sequence': insert_sequence,
                'es_encabezado_capitulo': False,
                'es_encabezado_seccion': False,
            }
            
            _logger.info(f"DEBUG ADD_PRODUCT: Valores para nueva línea: {new_line_vals}")
            
            # Crear la línea con contexto especial para evitar restricciones
            _logger.info(f"DEBUG ADD_PRODUCT: Creando línea con contexto from_capitulo_wizard=True")
            new_line = self.env['sale.order.line'].with_context(
                from_capitulo_wizard=True
            ).create(new_line_vals)
            
            _logger.info(f"DEBUG ADD_PRODUCT: ✅ Línea creada exitosamente con ID: {new_line.id}")
            
        except Exception as e:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ Error al crear línea: {str(e)}")
            import traceback
            _logger.error(f"DEBUG ADD_PRODUCT: Traceback completo: {traceback.format_exc()}")
            raise UserError(f"Error al crear la línea de producto: {str(e)}")
        
        # === FINALIZACIÓN Y RECÁLCULO ===
        # Forzar la escritura de los datos pendientes sin commit
        self.env.cr.flush()
        
        # Refrescar el record completo desde la base de datos
        order.invalidate_recordset()
        # Forzar el recálculo del campo computed
        order._compute_capitulos_agrupados()
        
        # === LOGGING DE CONFIRMACIÓN ===
        _logger.info(f"DEBUG: Producto añadido exitosamente. ID de nueva línea: {new_line.id}")
        _logger.info(f"DEBUG: Secuencia de nueva línea: {new_line.sequence}")
        _logger.info(f"DEBUG: Total de líneas en el pedido: {len(order.order_line)}")
        _logger.info(f"DEBUG: Campo capitulos_agrupados recalculado: {len(order.capitulos_agrupados)} caracteres")
        
        # Verificar que la nueva línea está en order_line
        if new_line.id in order.order_line.ids:
            _logger.info(f"DEBUG: ✓ Nueva línea confirmada en order_line")
        else:
            _logger.error(f"DEBUG: ✗ Nueva línea NO encontrada en order_line")
        
        return {
            'success': True,
            'message': f'Producto {product.name} añadido a {seccion_name}',
            'line_id': new_line.id
        }
    
    @api.model
    def save_condiciones_particulares(self, order_id, capitulo_name, seccion_name, condiciones_text):
        """
        Guarda las condiciones particulares de una sección específica.
        
        PROPÓSITO:
        - Permitir la edición de texto libre en secciones de "condiciones particulares"
        - Persistir información textual específica por sección
        - Proporcionar flexibilidad para contenido no estructurado
        
        PARÁMETROS:
        - order_id (int): ID del presupuesto
        - capitulo_name (str): Nombre del capítulo contenedor
        - seccion_name (str): Nombre de la sección objetivo
        - condiciones_text (str): Texto libre a guardar
        
        LÓGICA:
        1. Validación del presupuesto
        2. Búsqueda de la sección específica
        3. Actualización del campo condiciones_particulares
        4. Logging de la operación
        
        VALIDACIONES:
        - Existencia del presupuesto
        - Existencia de la sección en el capítulo
        
        RETORNO:
        - Dict con resultado de la operación
        
        REFERENCIAS:
        - static/src/js/capitulos_accordion_widget.js: Llama a este método
        - controllers/main.py: Expone este método vía HTTP
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"DEBUG SAVE_CONDICIONES: Guardando condiciones para capítulo '{capitulo_name}', sección '{seccion_name}'")
        _logger.info(f"DEBUG SAVE_CONDICIONES: Texto: {condiciones_text[:100]}...")
        
        order = self.browse(order_id)
        order.ensure_one()
        
        # Buscar la línea de la sección específica
        seccion_line = None
        for line in order.order_line.sorted('sequence'):
            if line.es_encabezado_seccion:
                line_base_name = self._get_base_name(line.name)
                seccion_base_name = self._get_base_name(seccion_name)
                
                if line_base_name.upper() == seccion_base_name.upper():
                    seccion_line = line
                    break
        
        if not seccion_line:
            _logger.error(f"DEBUG SAVE_CONDICIONES: ❌ No se encontró la sección '{seccion_name}'")
            raise UserError(f"No se encontró la sección: {seccion_name}")
        
        try:
            # Guardar las condiciones particulares en la línea de sección
            seccion_line.with_context(from_capitulo_wizard=True).condiciones_particulares = condiciones_text
            _logger.info(f"DEBUG SAVE_CONDICIONES: ✅ Condiciones guardadas en línea {seccion_line.id}")
            
            return {
                'success': True,
                'message': f'Condiciones particulares guardadas para {seccion_name}'
            }
            
        except Exception as e:
            _logger.error(f"DEBUG SAVE_CONDICIONES: ❌ Error al guardar: {str(e)}")
            raise UserError(f"Error al guardar las condiciones particulares: {str(e)}")


class SaleOrderLine(models.Model):
    """
    Extensión del modelo sale.order.line para soportar estructura de capítulos.
    
    HERENCIA: sale.order.line
    FUNCIONALIDAD: Control de integridad estructural y campos específicos de capítulos
    
    CAMPOS AÑADIDOS:
    - es_encabezado_capitulo: Flag para identificar encabezados de capítulo
    - es_encabezado_seccion: Flag para identificar encabezados de sección
    - condiciones_particulares: Campo de texto libre para secciones específicas
    
    VALIDACIONES IMPLEMENTADAS:
    - Prevención de eliminación de encabezados estructurales
    - Control de modificación de campos críticos en encabezados
    - Restricciones de creación manual de encabezados
    - Validación de contexto para operaciones del wizard
    
    MÉTODOS SOBRESCRITOS:
    - unlink(): Previene eliminación de encabezados
    - write(): Controla modificación de campos protegidos
    - create(): Valida creación de nuevas líneas
    
    CONTEXTOS ESPECIALES:
    - from_capitulo_wizard: Permite operaciones desde el wizard de capítulos
    - Bypass de validaciones para operaciones controladas
    
    REFERENCIAS:
    - wizard/capitulo_wizard.py: Usa contexto especial para operaciones
    - controllers/main.py: Operaciones CRUD controladas
    - models/sale_order.py: Métodos que manipulan líneas
    """
    _inherit = 'sale.order.line'
    
    # Flag para identificar líneas que son encabezados de capítulo
    es_encabezado_capitulo = fields.Boolean(
        string='Es Encabezado de Capítulo',
        default=False,
        help="Indica si esta línea es un encabezado de capítulo (no modificable)"
    )
    
    # Flag para identificar líneas que son encabezados de sección
    es_encabezado_seccion = fields.Boolean(
        string='Es Encabezado de Sección',
        default=False,
        help="Indica si esta línea es un encabezado de sección (no modificable)"
    )
    
    # Campo de texto libre para condiciones particulares de secciones
    condiciones_particulares = fields.Text(
        string='Condiciones Particulares',
        help="Texto libre para condiciones particulares de esta sección"
    )
    
    def unlink(self):
        """Previene la eliminación de encabezados de capítulos y secciones"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"DEBUG UNLINK: Intentando eliminar {len(self)} líneas")
        _logger.info(f"DEBUG UNLINK: Contexto completo: {dict(self.env.context)}")
        _logger.info(f"DEBUG UNLINK: from_capitulo_widget: {self.env.context.get('from_capitulo_widget')}")
        
        for line in self:
            _logger.info(f"DEBUG UNLINK: Línea {line.id} - '{line.name}' - Capítulo: {line.es_encabezado_capitulo}, Sección: {line.es_encabezado_seccion}")
        
        # Verificar si alguna línea es un encabezado
        headers_to_delete = self.filtered(lambda l: l.es_encabezado_capitulo or l.es_encabezado_seccion)
        
        if headers_to_delete:
            header_names = ', '.join(headers_to_delete.mapped('name'))
            _logger.error(f"DEBUG UNLINK: Intentando eliminar encabezados: {header_names}")
            raise UserError(
                f"No se pueden eliminar los siguientes encabezados: {header_names}\n"
                "Los encabezados de capítulos y secciones son elementos estructurales del presupuesto."
            )
        
        # Si llegamos aquí, todas las líneas son productos normales
        _logger.info("DEBUG UNLINK: Todas las líneas son productos normales, procediendo con eliminación")
        
        try:
            result = super().unlink()
            _logger.info("DEBUG UNLINK: Eliminación exitosa")
            return result
        except Exception as e:
            _logger.error(f"DEBUG UNLINK: Error durante eliminación: {str(e)}")
            raise e
    
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
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"DEBUG CREATE: Creando línea con valores: {vals}")
        _logger.info(f"DEBUG CREATE: Contexto: {dict(self.env.context)}")
        _logger.info(f"DEBUG CREATE: from_capitulo_wizard: {self.env.context.get('from_capitulo_wizard')}")
        
        # Si se está creando desde el wizard de capítulos, permitir la creación
        if self.env.context.get('from_capitulo_wizard'):
            _logger.info(f"DEBUG CREATE: ✅ Creación permitida por contexto from_capitulo_wizard")
            try:
                result = super().create(vals)
                _logger.info(f"DEBUG CREATE: ✅ Línea creada exitosamente con ID: {result.id}")
                return result
            except Exception as e:
                _logger.error(f"DEBUG CREATE: ❌ Error en super().create(): {str(e)}")
                import traceback
                _logger.error(f"DEBUG CREATE: Traceback: {traceback.format_exc()}")
                raise e
        
        # Bloquear la creación manual de encabezados de capítulos y secciones
        if vals.get('es_encabezado_capitulo') or vals.get('es_encabezado_seccion'):
            _logger.error(f"DEBUG CREATE: ❌ Intento de crear encabezado manualmente")
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
                    _logger.error(f"DEBUG CREATE: ❌ Intento de crear sección/nota con capítulos estructurados")
                    raise UserError(
                        "No se pueden añadir secciones o notas manualmente cuando el presupuesto tiene capítulos estructurados.\n"
                        "Use el botón 'Gestionar Capítulos' para gestionar la estructura."
                    )
        
        _logger.info(f"DEBUG CREATE: ✅ Validaciones pasadas, creando línea normal")
        try:
            result = super().create(vals)
            _logger.info(f"DEBUG CREATE: ✅ Línea normal creada exitosamente con ID: {result.id}")
            return result
        except Exception as e:
            _logger.error(f"DEBUG CREATE: ❌ Error en super().create() para línea normal: {str(e)}")
            import traceback
            _logger.error(f"DEBUG CREATE: Traceback: {traceback.format_exc()}")
            raise e