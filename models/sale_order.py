# -*- coding: utf-8 -*-
"""
Extensión del Modelo Sale Order para Capítulos Técnicos
=======================================================

Este módulo extiende el modelo sale.order de Odoo para integrar la funcionalidad
de capítulos técnicos. Permite aplicar capítulos estructurados a pedidos de venta,
organizando los productos en una jerarquía de capítulos y secciones.

Funcionalidades principales:
- Aplicación de capítulos técnicos a pedidos de venta
- Agrupación automática de líneas por capítulos y secciones
- Widget acordeón para navegación visual en la interfaz
- Gestión de productos por categorías dentro de secciones
- Cálculo automático de totales por capítulo

Autor: Sergio
Fecha: 2024
Versión: 1.0
"""

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """
    Extensión del modelo sale.order para integrar capítulos técnicos.
    
    Esta extensión añade la capacidad de aplicar capítulos estructurados a los pedidos
    de venta, organizando los productos en una jerarquía clara y proporcionando
    herramientas de navegación visual para mejorar la experiencia del usuario.
    
    Características añadidas:
    - Relación Many2many con capítulos técnicos
    - Campo computado para agrupación de líneas en formato JSON
    - Métodos para gestión de capítulos y secciones
    - Integración con widget acordeón para la interfaz
    - Soporte para categorías de productos por sección
    """
    _inherit = 'sale.order'

    # ========================================
    # CAMPOS DE RELACIÓN CON CAPÍTULOS
    # ========================================
    
    capitulo_ids = fields.Many2many(
        'capitulo.contrato', 
        string='Capítulos Aplicados',
        help="Capítulos técnicos aplicados a este pedido de venta. "
             "Cada capítulo define una estructura de secciones y productos"
    )
    
    # ========================================
    # CAMPOS COMPUTADOS PARA LA INTERFAZ
    # ========================================
    
    capitulos_agrupados = fields.Text(
        string='Capítulos Agrupados',
        compute='_compute_capitulos_agrupados',
        help="Datos en formato JSON con las líneas agrupadas por capítulo y sección "
             "para el widget acordeón. Se recalcula automáticamente cuando cambian las líneas"
    )
    
    tiene_multiples_capitulos = fields.Boolean(
        string='Mostrar Acordeón de Capítulos',
        compute='_compute_tiene_multiples_capitulos',
        help="Indica si el pedido tiene uno o más capítulos aplicados para mostrar "
             "el widget acordeón en la interfaz"
    )

    # ========================================
    # MÉTODOS AUXILIARES
    # ========================================

    def _get_base_name(self, decorated_name):
        """
        Extrae el nombre base de un capítulo o sección eliminando decoraciones.
        
        Este método normaliza los nombres de capítulos y secciones eliminando
        sufijos decorativos, contadores y caracteres especiales para permitir
        comparaciones consistentes entre nombres.
        
        Args:
            decorated_name (str): Nombre decorado que puede contener sufijos como
                                "(SECCIÓN FIJA)", contadores "(2)", o caracteres especiales
        
        Returns:
            str: Nombre base limpio sin decoraciones
            
        Ejemplos:
            "Materiales Eléctricos (SECCIÓN FIJA)" -> "Materiales Eléctricos"
            "Capítulo Principal (2)" -> "Capítulo Principal"
            "═══ Sección Especial ═══" -> "Sección Especial"
        """
        import re
        name = str(decorated_name)
        
        # 1. Eliminar sufijos como (SECCIÓN FIJA) o contadores numéricos
        name = re.sub(r'\s*\((SECCIÓN FIJA|\d+)\)$', '', name).strip()
        
        # 2. Eliminar caracteres decorativos de los extremos
        decorative_chars = ' \t\n\r=═🔒📋'
        name = name.strip(decorative_chars)
        
        return name
    
    # ========================================
    # MÉTODOS COMPUTADOS
    # ========================================
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo', 'order_line.es_encabezado_seccion', 
                 'order_line.name', 'order_line.product_id', 'order_line.product_uom_qty', 
                 'order_line.product_uom', 'order_line.price_unit', 'order_line.price_subtotal', 'order_line.sequence')
    def _compute_capitulos_agrupados(self):
        """
        Agrupa las líneas del pedido por capítulos y secciones para el widget acordeón.
        
        Este método es el núcleo del sistema de capítulos. Procesa todas las líneas del pedido
        y las organiza en una estructura jerárquica de capítulos > secciones > productos,
        generando un JSON que alimenta el widget acordeón en la interfaz.
        
        Proceso de agrupación:
        1. Recorre las líneas ordenadas por secuencia
        2. Identifica encabezados de capítulos y crea nuevas agrupaciones
        3. Identifica encabezados de secciones dentro de cada capítulo
        4. Agrupa productos bajo la sección correspondiente
        5. Calcula totales por capítulo
        6. Busca categorías de productos para filtrado automático
        
        Decorador @api.depends:
        - Se recalcula cuando cambian las líneas del pedido
        - Monitorea cambios en campos específicos de las líneas
        - Asegura sincronización automática con la interfaz
        
        Estructura del JSON generado:
        {
            "Nombre Capítulo": {
                "sections": {
                    "Nombre Sección": {
                        "lines": [lista de productos],
                        "condiciones_particulares": "texto",
                        "category_id": id_categoria,
                        "category_name": "nombre_categoria"
                    }
                },
                "total": importe_total_capitulo
            }
        }
        
        Manejo de duplicados:
        - Permite múltiples capítulos con el mismo nombre
        - Añade contadores automáticos: "Capítulo (2)", "Capítulo (3)"
        - Mantiene unicidad en las claves del JSON
        """
        import json
        import logging
        _logger = logging.getLogger(__name__)
        
        for order in self:
            _logger.info(f"DEBUG COMPUTE: Procesando pedido {order.id} con {len(order.order_line)} líneas")
            
            # Inicializar estructuras de datos
            capitulos_dict = {}  # Diccionario principal de capítulos
            current_capitulo_key = None  # Capítulo actualmente procesándose
            current_seccion_name = None  # Sección actualmente procesándose
            capitulo_counter = {}  # Contador para capítulos duplicados
            
            # Procesar cada línea en orden de secuencia
            for line in order.order_line.sorted('sequence'):
                if line.es_encabezado_capitulo:
                    # ===== PROCESAMIENTO DE ENCABEZADO DE CAPÍTULO =====
                    # Crear clave única para permitir capítulos duplicados
                    base_name = line.name
                    if base_name not in capitulo_counter:
                        capitulo_counter[base_name] = 0
                    capitulo_counter[base_name] += 1
                    
                    # Generar clave única: nombre base + contador si hay duplicados
                    if capitulo_counter[base_name] == 1:
                        current_capitulo_key = base_name
                    else:
                        current_capitulo_key = f"{base_name} ({capitulo_counter[base_name]})"
                    
                    # Inicializar estructura del capítulo
                    capitulos_dict[current_capitulo_key] = {
                        'sections': {},  # Diccionario de secciones
                        'total': 0.0     # Total acumulado del capítulo
                    }
                    current_seccion_name = None  # Reset sección actual
                    
                elif line.es_encabezado_seccion and current_capitulo_key:
                    # ===== PROCESAMIENTO DE ENCABEZADO DE SECCIÓN =====
                    current_seccion_name = line.name
                    
                    # Buscar configuración de categoría para esta sección
                    category_id = None
                    category_name = None
                    
                    # Buscar en los capítulos aplicados la sección correspondiente
                    for capitulo in order.capitulo_ids:
                        for seccion in capitulo.seccion_ids:
                            # Comparar nombres normalizados (sin decoraciones)
                            seccion_base_name = self._get_base_name(seccion.name)
                            line_base_name = self._get_base_name(current_seccion_name)
                            
                            if seccion_base_name.upper() == line_base_name.upper():
                                if seccion.product_category_id:
                                    category_id = seccion.product_category_id.id
                                    category_name = seccion.product_category_id.name
                                break
                        if category_id:
                            break
                    
                    # Inicializar estructura de la sección
                    capitulos_dict[current_capitulo_key]['sections'][current_seccion_name] = {
                        'lines': [],  # Lista de productos en la sección
                        'condiciones_particulares': line.condiciones_particulares or '',
                        'category_id': category_id,      # Para filtrado automático
                        'category_name': category_name   # Para mostrar en interfaz
                    }
                    
                elif current_capitulo_key and current_seccion_name:
                    # ===== PROCESAMIENTO DE LÍNEA DE PRODUCTO =====
                    # Crear estructura de datos para el producto
                    line_data = {
                        'id': line.id,  # ID para edición directa
                        'sequence': line.sequence,
                        'product_name': line.product_id.name if line.product_id else '',
                        'name': line.name,  # Nombre mostrado en la línea
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.name if line.product_uom else '',
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal
                    }
                    
                    # Añadir producto a la sección actual
                    capitulos_dict[current_capitulo_key]['sections'][current_seccion_name]['lines'].append(line_data)
                    
                    # Acumular total del capítulo
                    capitulos_dict[current_capitulo_key]['total'] += line.price_subtotal
            
            # Generar JSON final
            result_json = json.dumps(capitulos_dict) if capitulos_dict else '{}'
            order.capitulos_agrupados = result_json
            
            # Logging detallado para debugging
            _logger.info(f"DEBUG COMPUTE: Pedido {order.id} - Resultado final:")
            _logger.info(f"DEBUG COMPUTE: - Capítulos encontrados: {len(capitulos_dict)}")
            _logger.info(f"DEBUG COMPUTE: - JSON generado: {len(result_json)} caracteres")
            
            if capitulos_dict:
                for cap_name, cap_data in capitulos_dict.items():
                    sections_count = len(cap_data.get('sections', {}))
                    total_lines = sum(len(sec.get('lines', [])) for sec in cap_data.get('sections', {}).values())
                    _logger.info(f"DEBUG COMPUTE: - Capítulo '{cap_name}': {sections_count} secciones, {total_lines} productos")
            else:
                _logger.info(f"DEBUG COMPUTE: - ❌ No se generaron capítulos")
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo')
    def _compute_tiene_multiples_capitulos(self):
        """
        Determina si el pedido tiene capítulos para mostrar el widget acordeón.
        
        Este método calcula si el pedido contiene uno o más capítulos aplicados,
        lo que determina si se debe mostrar el widget acordeón en la interfaz.
        
        Lógica:
        - Cuenta las líneas marcadas como encabezado de capítulo
        - Si hay 1 o más capítulos: muestra el acordeón
        - Si no hay capítulos: oculta el acordeón
        
        El campo se recalcula automáticamente cuando:
        - Se añaden o eliminan líneas del pedido
        - Cambia el estado es_encabezado_capitulo de alguna línea
        """
        for order in self:
            # Contar líneas que son encabezados de capítulo
            capitulos_count = len(order.order_line.filtered('es_encabezado_capitulo'))
            
            # Mostrar acordeón si hay al menos 1 capítulo
            order.tiene_multiples_capitulos = capitulos_count >= 1
    
    # ========================================
    # MÉTODOS DE ACCIÓN (INTERFAZ)
    # ========================================
    
    def action_add_capitulo(self):
        """
        Abre el wizard para gestionar capítulos del presupuesto.
        
        Este método se ejecuta cuando el usuario hace clic en el botón "Gestionar Capítulos"
        en la vista del pedido de venta. Abre una ventana modal con el wizard que permite
        seleccionar y aplicar capítulos al pedido.
        
        Returns:
            dict: Acción de ventana para abrir el wizard en modo modal
            
        Contexto pasado al wizard:
        - default_order_id: ID del pedido actual
        - active_id: ID del registro activo
        - active_model: Modelo del registro activo
        """
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestionar Capítulos del Presupuesto',
            'res_model': 'capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',  # Ventana modal
            'context': {
                'default_order_id': self.id,
                'active_id': self.id,
                'active_model': 'sale.order'
            }
        }
    
    def toggle_capitulo_collapse(self, capitulo_index):
        """
        Alterna el estado colapsado/expandido de un capítulo en el acordeón.
        
        Este método maneja la interacción del usuario con el widget acordeón,
        permitiendo expandir o colapsar capítulos individuales para mejorar
        la navegación en presupuestos con múltiples capítulos.
        
        Args:
            capitulo_index (int): Índice del capítulo en la lista (base 0)
            
        Returns:
            dict: Acción para recargar la vista y reflejar el cambio
            
        Nota: Este método modifica el JSON de capitulos_agrupados para
        persistir el estado de expansión entre recargas de página.
        """
        import json
        
        self.ensure_one()
        capitulos = json.loads(self.capitulos_agrupados or '[]')
        
        # Validar índice y alternar estado
        if 0 <= capitulo_index < len(capitulos):
            capitulos[capitulo_index]['collapsed'] = not capitulos[capitulo_index].get('collapsed', True)
            self.capitulos_agrupados = json.dumps(capitulos)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    @api.model
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """Añade un producto a una sección específica de un capítulo"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"DEBUG ADD_PRODUCT: Iniciando adición de producto {product_id} a capítulo '{capitulo_name}', sección '{seccion_name}'")
        
        order = self.browse(order_id)
        order.ensure_one()
        
        _logger.info(f"DEBUG ADD_PRODUCT: Pedido {order.id} tiene {len(order.order_line)} líneas antes de añadir")
        
        try:
            if not product_id:
                _logger.error(f"DEBUG ADD_PRODUCT: ❌ No se proporcionó product_id")
                raise UserError("Debe seleccionar un producto")
            
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                _logger.error(f"DEBUG ADD_PRODUCT: ❌ Producto {product_id} no existe")
                raise UserError("El producto seleccionado no existe")
                
            _logger.info(f"DEBUG ADD_PRODUCT: ✅ Producto encontrado: {product.name} (ID: {product.id})")
        except Exception as e:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ Error al validar producto: {str(e)}")
            raise e
        
        _logger.info(f"DEBUG ADD_PRODUCT: Producto encontrado: {product.name}")
        
        # Buscar la línea de encabezado del capítulo
        capitulo_line = None
        seccion_line = None
        
        _logger.info(f"DEBUG ADD_PRODUCT: Buscando capítulo '{capitulo_name}' y sección '{seccion_name}'")
        _logger.info(f"DEBUG ADD_PRODUCT: Líneas en el pedido:")
        for line in order.order_line.sorted('sequence'):
            _logger.info(f"DEBUG ADD_PRODUCT: - Línea {line.sequence}: '{line.name}' (Capítulo: {line.es_encabezado_capitulo}, Sección: {line.es_encabezado_seccion})")
        
        for line in order.order_line.sorted('sequence'):
            if line.es_encabezado_capitulo:
                line_base_name = self._get_base_name(line.name)
                capitulo_base_name = self._get_base_name(capitulo_name)
                
                _logger.info(f"DEBUG ADD_PRODUCT: Comparando capítulo base '{line_base_name}' con '{capitulo_base_name}'")
                
                if line_base_name.upper() == capitulo_base_name.upper():
                    capitulo_line = line
                    _logger.info(f"DEBUG ADD_PRODUCT: ✅ Capítulo encontrado: {line.name}")
                    break
        
        if capitulo_line:
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
        else:
            _logger.error(f"DEBUG ADD_PRODUCT: ❌ No se encontró el capítulo '{capitulo_name}'")
        
        if not capitulo_line:
            raise UserError(f"No se encontró el capítulo: {capitulo_name}")
        
        if not seccion_line:
            raise UserError(f"No se encontró la sección: {seccion_name} en el capítulo: {capitulo_name}")
        
        # VALIDACIÓN: Verificar si es una sección de solo texto (condiciones particulares)
        seccion_name_lower = seccion_name.lower().strip()
        if 'condiciones particulares' in seccion_name_lower:
            _logger.warning(f"DEBUG ADD_PRODUCT: ❌ Intento de añadir producto a sección de solo texto: '{seccion_name}'")
            raise UserError(f"No se pueden añadir productos a la sección '{seccion_name}'. Esta sección es solo para texto editable.")
        
        # Estrategia simplificada: insertar inmediatamente después del encabezado de sección
        # Esto garantiza que el producto aparezca en la sección correcta
        insert_sequence = seccion_line.sequence + 1
        _logger.info(f"DEBUG: Insertando producto inmediatamente después de la sección '{seccion_line.name}' (seq: {seccion_line.sequence})")
        _logger.info(f"DEBUG: Secuencia de inserción: {insert_sequence}")

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
        
        # Crear la nueva línea de producto
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
        
        # Forzar la escritura de los datos pendientes sin commit
        self.env.cr.flush()
        
        # Refrescar el record completo desde la base de datos
        order.invalidate_recordset()
        # Forzar el recálculo del campo computed
        order._compute_capitulos_agrupados()
        
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
        """Guarda las condiciones particulares de una sección específica"""
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