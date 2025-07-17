from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class CapitulosController(http.Controller):
    

    @http.route('/capitulos/add_product_to_section', type='json', auth='user', methods=['POST'])
    def add_product_to_section(self, order_id, capitulo_name, seccion_name, product_id, quantity=1.0):
        """Endpoint para añadir un producto a una sección específica"""
        try:
            # Validar parámetros
            if not order_id:
                return {'success': False, 'error': 'ID de pedido requerido'}
            
            if not capitulo_name:
                return {'success': False, 'error': 'Nombre de capítulo requerido'}
            
            if not seccion_name:
                return {'success': False, 'error': 'Nombre de sección requerido'}
            
            if not product_id:
                return {'success': False, 'error': 'ID de producto requerido'}
            
            # Obtener el pedido de venta
            order = request.env['sale.order'].browse(order_id)
            if not order.exists():
                return {'success': False, 'error': 'Pedido no encontrado'}
            
            # Verificar permisos
            if not request.env.user.has_group('sales_team.group_sale_salesman'):
                return {'success': False, 'error': 'Sin permisos para modificar pedidos'}
            
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
    
    @http.route('/capitulos/search_products', type='json', auth='user', methods=['POST'])
    def search_products(self, query='', limit=10):
        """Endpoint para buscar productos"""
        try:
            domain = [('sale_ok', '=', True)]
            
            if query:
                domain.append(('name', 'ilike', query))
            
            products = request.env['product.product'].search(domain, limit=limit)
            
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