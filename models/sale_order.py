# -*- coding: utf-8 -*-

"""
MÓDULO DE GESTIÓN DE CAPÍTULOS EN PRESUPUESTOS
==============================================

Este módulo extiende el modelo sale.order de Odoo para añadir funcionalidad
de gestión de capítulos estructurados en presupuestos de construcción.

CARACTERÍSTICAS PRINCIPALES:
1. Organización jerárquica: Capítulos > Secciones > Líneas de producto
2. Agrupación automática de líneas por capítulos
3. Interfaz de acordeón para visualización
4. Gestión de condiciones particulares por sección
5. Control de estructura para evitar modificaciones manuales

ESTRUCTURA DE DATOS:
- Capítulos: Agrupaciones principales (ej: "Obra Civil", "Instalaciones")
- Secciones: Subdivisiones dentro de cada capítulo (ej: "Cimentación", "Estructura")
- Líneas: Productos individuales con cantidad, precio y descripción

@author: Tu Nombre
@version: 1.0
@since: 2024
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    """
    MODELO EXTENDIDO DE PEDIDO DE VENTA
    ==================================
    
    Extiende sale.order para añadir funcionalidad de capítulos estructurados.
    Permite organizar las líneas del presupuesto en una jerarquía de capítulos
    y secciones para una mejor gestión y presentación.
    """
    _inherit = 'sale.order'

    # ===========================================
    # CAMPOS DEL MODELO
    # ===========================================
    
    capitulo_ids = fields.One2many(
        'sale.order.capitulo', 
        'order_id', 
        string='Capítulos',
        help="Capítulos asociados a este presupuesto"
    )
    
    capitulos_agrupados = fields.Text(
        string='Capítulos Agrupados',
        compute='_compute_capitulos_agrupados',
        store=False,
        help="JSON con la estructura de capítulos, secciones y líneas para el widget"
    )
    
    tiene_multiples_capitulos = fields.Boolean(
        string='Tiene Múltiples Capítulos',
        compute='_compute_tiene_multiples_capitulos',
        store=False,
        help="Indica si el presupuesto tiene múltiples capítulos para mostrar el acordeón"
    )

    # ===========================================
    # MÉTODOS COMPUTADOS
    # ===========================================

    def _get_base_name(self, name):
        """
        EXTRACTOR DE NOMBRE BASE
        =======================
        
        Extrae el nombre base de un capítulo o sección eliminando prefijos numéricos.
        
        Args:
            name (str): Nombre completo con posible prefijo numérico
            
        Returns:
            str: Nombre base sin prefijo numérico
            
        Ejemplo:
            "01. Obra Civil" -> "Obra Civil"
            "1.1 Cimentación" -> "Cimentación"
        """
        if not name:
            return name
        
        # Eliminar prefijos como "01. ", "1.1 ", etc.
        import re
        pattern = r'^\d+(\.\d+)*\.\s*'
        return re.sub(pattern, '', name).strip()

    @api.depends('order_line')
    def _compute_capitulos_agrupados(self):
        """
        COMPUTADOR DE CAPÍTULOS AGRUPADOS
        ================================
        
        Organiza las líneas del pedido en una estructura jerárquica de capítulos
        y secciones, generando un JSON que será utilizado por el widget frontend.
        
        Estructura del JSON generado:
        {
            "Capítulo 1": {
                "sections": {
                    "Sección 1": {
                        "lines": [...],
                        "category_id": 123,
                        "condiciones_particulares": "texto..."
                    }
                }
            }
        }
        """
        for order in self:
            try:
                capitulos_data = {}
                current_chapter = None
                current_section = None
                
                # Procesar cada línea del pedido en orden
                for line in order.order_line:
                    # Detectar encabezados de capítulo
                    if line.es_encabezado_capitulo:
                        current_chapter = self._get_base_name(line.name)
                        current_section = None
                        
                        # Inicializar estructura del capítulo
                        if current_chapter not in capitulos_data:
                            capitulos_data[current_chapter] = {
                                'sections': {}
                            }
                    
                    # Detectar encabezados de sección
                    elif line.es_encabezado_seccion:
                        if current_chapter:
                            current_section = self._get_base_name(line.name)
                            
                            # Inicializar estructura de la sección
                            if current_section not in capitulos_data[current_chapter]['sections']:
                                capitulos_data[current_chapter]['sections'][current_section] = {
                                    'lines': [],
                                    'category_id': line.product_id.categ_id.id if line.product_id else None,
                                    'condiciones_particulares': line.condiciones_particulares or ''
                                }
                    
                    # Procesar líneas de producto normales
                    elif current_chapter and current_section:
                        # Añadir línea a la sección actual
                        line_data = {
                            'id': line.id,
                            'product_name': line.product_id.name if line.product_id else line.name,
                            'description': line.name,
                            'quantity': line.product_uom_qty,
                            'price_unit': line.price_unit,
                            'price_subtotal': line.price_subtotal,
                            'product_uom': line.product_uom.name if line.product_uom else '',
                        }
                        capitulos_data[current_chapter]['sections'][current_section]['lines'].append(line_data)
                
                # Convertir a JSON para el widget
                order.capitulos_agrupados = json.dumps(capitulos_data, ensure_ascii=False)
                
            except Exception as e:
                _logger.error(f"Error computing capitulos_agrupados for order {order.id}: {str(e)}")
                order.capitulos_agrupados = '{}'

    @api.depends('order_line')
    def _compute_tiene_multiples_capitulos(self):
        """
        DETECTOR DE MÚLTIPLES CAPÍTULOS
        ==============================
        
        Determina si el presupuesto tiene múltiples capítulos para decidir
        si mostrar la interfaz de acordeón o la vista tradicional.
        """
        for order in self:
            # Contar encabezados de capítulo
            chapter_count = len(order.order_line.filtered('es_encabezado_capitulo'))
            order.tiene_multiples_capitulos = chapter_count > 1

    # ===========================================
    # MÉTODOS DE ACCIÓN
    # ===========================================

    def action_add_capitulo(self):
        """
        ACCIÓN PARA AÑADIR CAPÍTULO
        ==========================
        
        Abre el asistente para gestionar capítulos del presupuesto.
        
        Returns:
            dict: Acción de ventana para abrir el asistente
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Gestionar Capítulos'),
            'res_model': 'sale.order.capitulo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'active_id': self.id,
                'active_model': 'sale.order',
            }
        }

    def toggle_capitulo_collapse(self, capitulo_name):
        """
        ALTERNADOR DE ESTADO DE CAPÍTULO
        ===============================
        
        Alterna el estado expandido/colapsado de un capítulo específico.
        
        Args:
            capitulo_name (str): Nombre del capítulo a alternar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Buscar el capítulo por nombre
            capitulo = self.capitulo_ids.filtered(
                lambda c: self._get_base_name(c.name) == capitulo_name
            )
            
            if capitulo:
                # Alternar estado
                capitulo.collapsed = not capitulo.collapsed
                return {'success': True}
            else:
                return {'success': False, 'error': _('Capítulo no encontrado')}
                
        except Exception as e:
            _logger.error(f"Error toggling chapter collapse: {str(e)}")
            return {'success': False, 'error': str(e)}

    def add_product_to_section(self, chapter_name, section_name, product_id, quantity=1.0):
        """
        AÑADIR PRODUCTO A SECCIÓN
        ========================
        
        Añade un producto específico a una sección dentro de un capítulo,
        manteniendo la estructura jerárquica del presupuesto.
        
        Args:
            chapter_name (str): Nombre del capítulo destino
            section_name (str): Nombre de la sección destino
            product_id (int): ID del producto a añadir
            quantity (float): Cantidad del producto (por defecto 1.0)
            
        Returns:
            dict: Resultado de la operación con éxito/error
            
        Proceso:
        1. Busca el capítulo y sección especificados
        2. Valida que la sección permita productos
        3. Calcula la posición de inserción
        4. Crea la nueva línea de producto
        5. Recalcula los campos computados
        """
        try:
            _logger.info(f"Añadiendo producto {product_id} a {chapter_name}/{section_name}")
            
            # ===================================
            # BÚSQUEDA DE CAPÍTULO Y SECCIÓN
            # ===================================
            
            chapter_line = None
            section_line = None
            insert_position = 0
            
            # Buscar líneas de encabezado
            for i, line in enumerate(self.order_line):
                if line.es_encabezado_capitulo and self._get_base_name(line.name) == chapter_name:
                    chapter_line = line
                    _logger.info(f"Capítulo encontrado: {line.name}")
                    
                elif (chapter_line and line.es_encabezado_seccion and 
                      self._get_base_name(line.name) == section_name):
                    section_line = line
                    insert_position = i + 1
                    _logger.info(f"Sección encontrada: {line.name} en posición {insert_position}")
                    break
            
            # Validaciones
            if not chapter_line:
                return {
                    'success': False,
                    'error': f'Capítulo "{chapter_name}" no encontrado'
                }
            
            if not section_line:
                return {
                    'success': False,
                    'error': f'Sección "{section_name}" no encontrada en el capítulo "{chapter_name}"'
                }
            
            # ===================================
            # VALIDACIÓN DE SECCIÓN
            # ===================================
            
            # Verificar que la sección no sea de solo texto
            if section_line.condiciones_particulares and not section_line.product_id:
                return {
                    'success': False,
                    'error': 'No se pueden añadir productos a secciones de condiciones particulares'
                }
            
            # ===================================
            # CÁLCULO DE POSICIÓN DE INSERCIÓN
            # ===================================
            
            # Buscar la posición correcta después de las líneas existentes de la sección
            for i in range(insert_position, len(self.order_line)):
                line = self.order_line[i]
                
                # Si encontramos otro encabezado, insertar antes
                if line.es_encabezado_capitulo or line.es_encabezado_seccion:
                    insert_position = i
                    break
                else:
                    # Continuar después de las líneas existentes
                    insert_position = i + 1
            
            # ===================================
            # DESPLAZAMIENTO DE LÍNEAS EXISTENTES
            # ===================================
            
            # Incrementar la secuencia de las líneas posteriores
            lines_to_update = self.order_line.filtered(
                lambda l: l.sequence >= insert_position * 10
            )
            for line in lines_to_update:
                line.sequence += 10
            
            # ===================================
            # CREACIÓN DE LA NUEVA LÍNEA
            # ===================================
            
            # Obtener información del producto
            product = self.env['product.product'].browse(product_id)
            if not product.exists():
                return {
                    'success': False,
                    'error': f'Producto con ID {product_id} no encontrado'
                }
            
            # Crear la nueva línea de producto
            new_line_vals = {
                'order_id': self.id,
                'product_id': product_id,
                'name': product.name,
                'product_uom_qty': quantity,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
                'sequence': insert_position * 10,
                'es_encabezado_capitulo': False,
                'es_encabezado_seccion': False,
            }
            
            new_line = self.env['sale.order.line'].create(new_line_vals)
            _logger.info(f"Nueva línea creada: {new_line.id}")
            
            # ===================================
            # RECÁLCULO Y FINALIZACIÓN
            # ===================================
            
            # Forzar recálculo de campos computados
            self._compute_capitulos_agrupados()
            self._compute_tiene_multiples_capitulos()
            
            return {
                'success': True,
                'message': f'Producto "{product.name}" añadido correctamente a {section_name}',
                'line_id': new_line.id
            }
            
        except Exception as e:
            _logger.error(f"Error añadiendo producto a sección: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }

    def save_condiciones_particulares(self, chapter_name, section_name, text):
        """
        GUARDAR CONDICIONES PARTICULARES
        ===============================
        
        Guarda el texto de condiciones particulares en una sección específica.
        
        Args:
            chapter_name (str): Nombre del capítulo
            section_name (str): Nombre de la sección
            text (str): Texto de las condiciones particulares
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Buscar la línea de encabezado de sección
            section_line = None
            chapter_found = False
            
            for line in self.order_line:
                if line.es_encabezado_capitulo and self._get_base_name(line.name) == chapter_name:
                    chapter_found = True
                elif (chapter_found and line.es_encabezado_seccion and 
                      self._get_base_name(line.name) == section_name):
                    section_line = line
                    break
            
            if not section_line:
                return {
                    'success': False,
                    'error': f'Sección "{section_name}" no encontrada'
                }
            
            # Actualizar las condiciones particulares
            section_line.condiciones_particulares = text
            
            # Recalcular campos computados
            self._compute_capitulos_agrupados()
            
            return {
                'success': True,
                'message': 'Condiciones particulares guardadas correctamente'
            }
            
        except Exception as e:
            _logger.error(f"Error guardando condiciones particulares: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }


class SaleOrderLine(models.Model):
    """
    MODELO EXTENDIDO DE LÍNEA DE PEDIDO
    ==================================
    
    Extiende sale.order.line para añadir campos específicos de la estructura
    de capítulos y controlar la integridad de los datos.
    """
    _inherit = 'sale.order.line'

    # ===========================================
    # CAMPOS ADICIONALES
    # ===========================================
    
    es_encabezado_capitulo = fields.Boolean(
        string='Es Encabezado de Capítulo',
        default=False,
        help="Indica si esta línea es un encabezado de capítulo"
    )
    
    es_encabezado_seccion = fields.Boolean(
        string='Es Encabezado de Sección',
        default=False,
        help="Indica si esta línea es un encabezado de sección"
    )
    
    condiciones_particulares = fields.Text(
        string='Condiciones Particulares',
        help="Texto libre para condiciones particulares de la sección"
    )

    # ===========================================
    # MÉTODOS DE CONTROL DE INTEGRIDAD
    # ===========================================

    def unlink(self):
        """
        CONTROL DE ELIMINACIÓN
        =====================
        
        Previene la eliminación manual de encabezados de capítulos y secciones
        para mantener la integridad de la estructura.
        """
        # Verificar si alguna línea es encabezado
        headers = self.filtered(lambda l: l.es_encabezado_capitulo or l.es_encabezado_seccion)
        
        if headers:
            raise UserError(_(
                'No se pueden eliminar encabezados de capítulos o secciones manualmente. '
                'Use el asistente de gestión de capítulos.'
            ))
        
        return super().unlink()

    def write(self, vals):
        """
        CONTROL DE MODIFICACIÓN
        ======================
        
        Controla las modificaciones en líneas de encabezado para prevenir
        cambios que rompan la estructura.
        """
        # Verificar modificaciones en encabezados
        headers = self.filtered(lambda l: l.es_encabezado_capitulo or l.es_encabezado_seccion)
        
        if headers and any(key in vals for key in ['product_id', 'product_uom_qty', 'price_unit']):
            raise UserError(_(
                'No se pueden modificar los campos de producto en encabezados de capítulos o secciones.'
            ))
        
        return super().write(vals)

    @api.model
    def create(self, vals):
        """
        CONTROL DE CREACIÓN
        ==================
        
        Controla la creación de nuevas líneas en pedidos con estructura de capítulos.
        """
        # Si el pedido tiene capítulos estructurados, validar la creación
        if vals.get('order_id'):
            order = self.env['sale.order'].browse(vals['order_id'])
            
            # Si tiene capítulos y no es un encabezado, verificar contexto
            if (order.tiene_multiples_capitulos and 
                not vals.get('es_encabezado_capitulo') and 
                not vals.get('es_encabezado_seccion') and
                not self.env.context.get('skip_structure_validation')):
                
                # Permitir solo si se está usando el método add_product_to_section
                if not self.env.context.get('adding_to_section'):
                    raise UserError(_(
                        'En presupuestos con capítulos estructurados, use el botón "Añadir Producto" '
                        'para mantener la organización correcta.'
                    ))
        
        return super().create(vals)