# -*- coding: utf-8 -*-

"""
CONTROLADOR WEB PARA EL MÓDULO DE CAPÍTULOS TÉCNICOS
===================================================

Este controlador proporciona endpoints HTTP/JSON para la gestión dinámica
de capítulos técnicos desde el frontend de Odoo. Permite operaciones
como añadir productos a secciones y buscar productos de forma asíncrona.

ENDPOINTS DISPONIBLES:
1. /capitulos/add_product_to_section - Añadir productos a secciones específicas
2. /capitulos/search_products - Búsqueda de productos con filtros

CARACTERÍSTICAS:
- Autenticación requerida para todos los endpoints
- Validación de permisos de usuario
- Manejo robusto de errores
- Logging detallado para debugging
- Respuestas JSON estructuradas

SEGURIDAD:
- Verificación de permisos de ventas
- Validación de parámetros de entrada
- Control de acceso a pedidos
- Manejo seguro de excepciones

@author: Sergio Vadillo
@version: 18.0.1.1.0
@since: 2024
@license: LGPL-3
"""

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class CapitulosController(http.Controller):
    """
    CONTROLADOR PRINCIPAL DE CAPÍTULOS TÉCNICOS
    ==========================================
    
    Maneja las peticiones HTTP/JSON relacionadas con la gestión
    de capítulos técnicos en presupuestos de venta.
    """

    @http.route('/capitulos/add_product_to_section', type='json', auth='user', methods=['POST'])
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """
        ENDPOINT PARA AÑADIR PRODUCTO A SECCIÓN
        ======================================
        
        Permite añadir un producto específico a una sección dentro de un capítulo
        del presupuesto, manteniendo la estructura jerárquica.
        
        Args:
            order_id (int): ID del pedido de venta
            capitulo_name (str): Nombre del capítulo destino
            seccion_name (str): Nombre de la sección destino
            product_id (int): ID del producto a añadir
            quantity (float, optional): Cantidad del producto (por defecto 1.0)
            
        Returns:
            dict: Resultado de la operación con estructura:
                {
                    'success': bool,
                    'message': str (si success=True),
                    'error': str (si success=False),
                    'line_id': int (si success=True)
                }
                
        Validaciones:
        - Parámetros requeridos presentes
        - Existencia del pedido de venta
        - Permisos de usuario para modificar pedidos
        - Valores numéricos válidos
        
        Ejemplo de uso:
            POST /capitulos/add_product_to_section
            {
                "order_id": 123,
                "capitulo_name": "Obra Civil",
                "seccion_name": "Cimentación",
                "product_id": 456,
                "quantity": 2.5
            }
        """
        try:
            # ===================================
            # VALIDACIÓN DE PARÁMETROS
            # ===================================
            
            if not order_id:
                return {'success': False, 'error': 'ID de pedido requerido'}
            
            if not capitulo_name:
                return {'success': False, 'error': 'Nombre de capítulo requerido'}
            
            if not seccion_name:
                return {'success': False, 'error': 'Nombre de sección requerido'}
            
            if not product_id:
                return {'success': False, 'error': 'ID de producto requerido'}
            
            # ===================================
            # VALIDACIÓN DE PEDIDO
            # ===================================
            
            # Obtener el pedido de venta
            order = request.env['sale.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Pedido no encontrado'}
            
            # ===================================
            # VALIDACIÓN DE PERMISOS
            # ===================================
            
            # Verificar permisos de usuario
            if not request.env.user.has_group('sales_team.group_sale_salesman'):
                return {'success': False, 'error': 'Sin permisos para modificar pedidos'}
            
            # ===================================
            # PROCESAMIENTO DE LA SOLICITUD
            # ===================================
            
            # Llamar al método del modelo para añadir el producto
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
    
    @http.route('/capitulos/search_products', type='json', auth='user', methods=['POST'])
    def search_products(self, query='', limit=10):
        """
        ENDPOINT PARA BÚSQUEDA DE PRODUCTOS
        ==================================
        
        Proporciona funcionalidad de búsqueda de productos para el frontend,
        con filtros y límites configurables.
        
        Args:
            query (str, optional): Término de búsqueda para filtrar productos
            limit (int, optional): Número máximo de resultados (por defecto 10)
            
        Returns:
            dict: Resultado de la búsqueda con estructura:
                {
                    'success': bool,
                    'products': list (si success=True),
                    'error': str (si success=False)
                }
                
        Estructura de cada producto en la lista:
            {
                'id': int,
                'name': str,
                'default_code': str,
                'list_price': float,
                'uom_name': str
            }
            
        Filtros aplicados:
        - Solo productos vendibles (sale_ok=True)
        - Búsqueda por nombre (si se proporciona query)
        - Límite de resultados configurable
        
        Ejemplo de uso:
            POST /capitulos/search_products
            {
                "query": "tornillo",
                "limit": 20
            }
        """
        try:
            # ===================================
            # CONSTRUCCIÓN DEL DOMINIO DE BÚSQUEDA
            # ===================================
            
            # Filtro base: solo productos vendibles
            domain = [('sale_ok', '=', True)]
            
            # Añadir filtro de búsqueda si se proporciona
            if query:
                domain.append(('name', 'ilike', query))
            
            # ===================================
            # BÚSQUEDA DE PRODUCTOS
            # ===================================
            
            # Ejecutar búsqueda con límite
            products = request.env['product.product'].search(domain, limit=limit)
            
            # ===================================
            # FORMATEO DE RESULTADOS
            # ===================================
            
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