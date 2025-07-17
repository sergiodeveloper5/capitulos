# -*- coding: utf-8 -*-
"""
Controladores Web para Módulo de Capítulos Técnicos
===================================================

Este módulo contiene los controladores web que proporcionan endpoints HTTP/JSON
para la funcionalidad de capítulos técnicos. Estos controladores permiten la
interacción entre el frontend JavaScript y el backend de Odoo.

Controladores incluidos:
- CapitulosController: Controlador principal para operaciones de capítulos

Endpoints disponibles:
- /capitulos/add_product_to_section: Añadir productos a secciones
- /capitulos/search_products: Búsqueda de productos
- /capitulos/search_categories: Búsqueda de categorías

Funcionalidades principales:
- Validación de parámetros de entrada
- Control de permisos y autenticación
- Manejo de errores robusto
- Logging detallado para auditoría
- Respuestas JSON estructuradas

Autor: Sergio
Fecha: 2024
Versión: 1.0
"""

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class CapitulosController(http.Controller):
    """
    Controlador principal para la gestión de capítulos técnicos.
    
    Este controlador proporciona endpoints web para la interacción con el módulo
    de capítulos técnicos desde el frontend JavaScript. Maneja operaciones como
    añadir productos a secciones, búsqueda de productos y categorías.
    
    Características:
    - Autenticación requerida para todos los endpoints
    - Validación exhaustiva de parámetros
    - Control de permisos granular
    - Manejo de errores robusto
    - Logging detallado para debugging
    - Respuestas JSON consistentes
    """

    # ========================================
    # ENDPOINTS PARA GESTIÓN DE PRODUCTOS
    # ========================================

    @http.route('/capitulos/add_product_to_section', type='json', auth='user', methods=['POST'])
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """
        Endpoint para añadir un producto a una sección específica de un capítulo.
        
        Este endpoint permite añadir productos a secciones de capítulos desde el
        frontend JavaScript, validando todos los parámetros y permisos necesarios.
        
        Args:
            order_id (int): ID del pedido de venta
            capitulo_name (str): Nombre del capítulo
            seccion_name (str): Nombre de la sección
            product_id (int): ID del producto a añadir
            quantity (float, optional): Cantidad del producto. Defaults to 1.0.
            
        Returns:
            dict: Respuesta JSON con el resultado de la operación
                - success (bool): True si la operación fue exitosa
                - error (str): Mensaje de error si success es False
                - data (dict): Datos adicionales si success es True
                
        Raises:
            ValueError: Si los parámetros no son válidos
            Exception: Para otros errores durante la operación
            
        Security:
            - Requiere autenticación de usuario
            - Valida permisos de ventas
            - Verifica existencia del pedido
        """
        try:
            # ========================================
            # VALIDACIÓN DE PARÁMETROS DE ENTRADA
            # ========================================
            
            if not order_id:
                return {'success': False, 'error': 'ID de pedido requerido'}
            
            if not capitulo_name:
                return {'success': False, 'error': 'Nombre de capítulo requerido'}
            
            if not seccion_name:
                return {'success': False, 'error': 'Nombre de sección requerido'}
            
            if not product_id:
                return {'success': False, 'error': 'ID de producto requerido'}
            
            # ========================================
            # VALIDACIÓN DE EXISTENCIA Y PERMISOS
            # ========================================
            
            # Obtener el pedido de venta
            order = request.env['sale.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Pedido no encontrado'}
            
            # Verificar permisos
            if not request.env.user.has_group('sales_team.group_sale_salesman'):
                return {'success': False, 'error': 'Sin permisos para modificar pedidos'}
            
            # ========================================
            # EJECUCIÓN DE LA OPERACIÓN
            # ========================================
            
            # Llamar al método del modelo
            result = order.add_product_to_section(
                capitulo_name=capitulo_name,
                seccion_name=seccion_name,
                product_id=int(product_id),
                quantity=float(quantity)
            )
            
            _logger.info(f"Producto añadido exitosamente: {result}")
            return result
            
        except ValueError as e:
            _logger.error(f"Error de valor en add_product_to_section: {str(e)}")
            return {'success': False, 'error': f'Error de valor: {str(e)}'}
        
        except Exception as e:
            _logger.error(f"Error en add_product_to_section: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ========================================
    # ENDPOINTS PARA BÚSQUEDA Y FILTRADO
    # ========================================
    
    @http.route('/capitulos/search_products', type='json', auth='user', methods=['POST'])
    def search_products(self, query='', limit=10):
        """
        Endpoint para buscar productos disponibles para venta.
        
        Este endpoint proporciona funcionalidad de búsqueda de productos para
        el selector de productos en el frontend. Permite filtrar productos
        por nombre y limitar los resultados.
        
        Args:
            query (str, optional): Término de búsqueda para filtrar productos. Defaults to ''.
            limit (int, optional): Número máximo de resultados. Defaults to 10.
            
        Returns:
            dict: Respuesta JSON con los productos encontrados
                - success (bool): True si la búsqueda fue exitosa
                - products (list): Lista de productos encontrados
                - error (str): Mensaje de error si success es False
                
        Product Structure:
            Cada producto en la lista contiene:
            - id (int): ID del producto
            - name (str): Nombre del producto
            - default_code (str): Código de referencia
            - list_price (float): Precio de lista
            - uom_name (str): Nombre de la unidad de medida
            
        Security:
            - Requiere autenticación de usuario
            - Solo muestra productos marcados como vendibles
        """
        try:
            # ========================================
            # CONSTRUCCIÓN DEL DOMINIO DE BÚSQUEDA
            # ========================================
            
            domain = [('sale_ok', '=', True)]  # Solo productos vendibles
            
            if query:
                domain.append(('name', 'ilike', query))
            
            # ========================================
            # EJECUCIÓN DE LA BÚSQUEDA
            # ========================================
            
            products = request.env['product.product'].search(domain, limit=limit)
            
            # ========================================
            # FORMATEO DE RESULTADOS
            # ========================================
            
            result = []
            for product in products:
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code or '',
                    'list_price': product.list_price,
                    'uom_name': product.uom_id.name
                })
            
            return {'success': True, 'products': result}
            
        except Exception as e:
            _logger.error(f"Error en search_products: {str(e)}")
            return {'success': False, 'error': str(e)}