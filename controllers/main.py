# -*- coding: utf-8 -*-
"""
CONTROLADOR HTTP PRINCIPAL PARA CAPÍTULOS CONTRATADOS
====================================================

Este archivo define los endpoints HTTP/JSON que permiten la comunicación
entre el frontend JavaScript y el backend Python del módulo.

FUNCIONALIDAD PRINCIPAL:
- Endpoints JSON para operaciones CRUD de productos en secciones
- Búsqueda de productos para el widget JavaScript
- Validación de permisos y parámetros
- Manejo de errores y logging

ENDPOINTS DISPONIBLES:
1. /capitulos/add_product_to_section: Añade producto a sección específica
2. /capitulos/search_products: Busca productos para autocompletado

COMUNICACIÓN:
- Frontend (JS) → HTTP POST → Backend (Python)
- Respuestas en formato JSON con estructura estándar
- Autenticación requerida (auth='user')

SEGURIDAD:
- Verificación de permisos de usuario
- Validación de parámetros de entrada
- Sanitización de datos
- Logging de operaciones

REFERENCIAS:
- models/sale_order.py: Método add_product_to_section()
- static/src/js/capitulos_accordion_widget.js: Llamadas AJAX
"""

from odoo import http
from odoo.http import request
import json
import logging

# Configuración de logging para debugging y monitoreo
_logger = logging.getLogger(__name__)

class CapitulosController(http.Controller):
    """
    Controlador principal para gestión de capítulos técnicos.
    
    Proporciona endpoints HTTP/JSON para la comunicación entre
    el widget JavaScript y los modelos Python del backend.
    """

    @http.route('/capitulos/add_product_to_section', type='json', auth='user', methods=['POST'])
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """
        ENDPOINT: Añadir producto a sección específica de un capítulo
        ===========================================================
        
        Permite al widget JavaScript añadir productos a secciones específicas
        de capítulos en un presupuesto de venta.
        
        PARÁMETROS:
        -----------
        order_id (int): ID del presupuesto de venta
        capitulo_name (str): Nombre del capítulo donde añadir
        seccion_name (str): Nombre de la sección donde añadir
        product_id (int): ID del producto a añadir
        quantity (float): Cantidad del producto (por defecto 1.0)
        
        RETORNA:
        --------
        dict: {
            'success': bool,        # True si la operación fue exitosa
            'line_id': int,         # ID de la línea creada (si success=True)
            'error': str            # Mensaje de error (si success=False)
        }
        
        FLUJO DE EJECUCIÓN:
        ------------------
        1. Validación de parámetros obligatorios
        2. Verificación de existencia del pedido
        3. Validación de permisos de usuario
        4. Llamada al método del modelo sale.order
        5. Logging y retorno de resultado
        
        PERMISOS REQUERIDOS:
        -------------------
        - Usuario autenticado (auth='user')
        - Grupo 'sales_team.group_sale_salesman'
        
        REFERENCIAS:
        -----------
        - models/sale_order.py: add_product_to_section()
        - static/src/js/capitulos_accordion_widget.js: addProductToSection()
        """
        try:
            # VALIDACIÓN DE PARÁMETROS OBLIGATORIOS
            if not order_id:
                return {'success': False, 'error': 'ID de pedido requerido'}
            
            if not capitulo_name:
                return {'success': False, 'error': 'Nombre de capítulo requerido'}
            
            if not seccion_name:
                return {'success': False, 'error': 'Nombre de sección requerido'}
            
            if not product_id:
                return {'success': False, 'error': 'ID de producto requerido'}
            
            # OBTENCIÓN Y VALIDACIÓN DEL PEDIDO DE VENTA
            order = request.env['sale.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Pedido no encontrado'}
            
            # VERIFICACIÓN DE PERMISOS DE USUARIO
            # Solo usuarios con permisos de ventas pueden modificar pedidos
            if not request.env.user.has_group('sales_team.group_sale_salesman'):
                return {'success': False, 'error': 'Sin permisos para modificar pedidos'}
            
            # LLAMADA AL MÉTODO DEL MODELO
            # Delega la lógica de negocio al modelo sale.order
            result = order.add_product_to_section(
                capitulo_name=capitulo_name,
                seccion_name=seccion_name,
                product_id=int(product_id),
                quantity=float(quantity)
            )
            
            # LOGGING DE OPERACIÓN EXITOSA
            _logger.info(f"Producto añadido exitosamente: {result}")
            return result
            
        except ValueError as e:
            # MANEJO DE ERRORES DE CONVERSIÓN DE TIPOS
            _logger.error(f"Error de valor en add_product_to_section: {str(e)}")
            return {'success': False, 'error': f'Error de valor: {str(e)}'}
        
        except Exception as e:
            # MANEJO DE ERRORES GENERALES
            _logger.error(f"Error en add_product_to_section: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/capitulos/search_products', type='json', auth='user', methods=['POST'])
    def search_products(self, query='', limit=10):
        """
        ENDPOINT: Búsqueda de productos para autocompletado
        =================================================
        
        Proporciona funcionalidad de búsqueda de productos para el
        widget JavaScript, utilizado en diálogos de selección.
        
        PARÁMETROS:
        -----------
        query (str): Término de búsqueda (opcional)
        limit (int): Número máximo de resultados (por defecto 10)
        
        RETORNA:
        --------
        dict: {
            'success': bool,        # True si la búsqueda fue exitosa
            'products': list,       # Lista de productos encontrados
            'error': str            # Mensaje de error (si success=False)
        }
        
        ESTRUCTURA DE PRODUCTOS:
        -----------------------
        Cada producto en la lista contiene:
        {
            'id': int,              # ID único del producto
            'name': str,            # Nombre del producto
            'default_code': str,    # Código/referencia del producto
            'list_price': float,    # Precio de lista
            'uom_name': str         # Nombre de la unidad de medida
        }
        
        FILTROS APLICADOS:
        -----------------
        - sale_ok = True: Solo productos vendibles
        - name ilike query: Búsqueda por nombre (si se proporciona query)
        
        REFERENCIAS:
        -----------
        - static/src/js/capitulos_accordion_widget.js: searchProducts()
        - models/product.py: Modelo product.product
        """
        try:
            # CONSTRUCCIÓN DEL DOMINIO DE BÚSQUEDA
            # Filtro base: solo productos vendibles
            domain = [('sale_ok', '=', True)]
            
            # Filtro adicional: búsqueda por nombre (si se proporciona)
            if query:
                domain.append(('name', 'ilike', query))
            
            # BÚSQUEDA EN BASE DE DATOS
            products = request.env['product.product'].search(domain, limit=limit)
            
            # CONSTRUCCIÓN DE RESPUESTA
            result = []
            for product in products:
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code or '',  # Código puede ser None
                    'list_price': product.list_price,
                    'uom_name': product.uom_id.name
                })
            
            return {'success': True, 'products': result}
            
        except Exception as e:
            # MANEJO DE ERRORES EN BÚSQUEDA
            _logger.error(f"Error en search_products: {str(e)}")
            return {'success': False, 'error': str(e)}