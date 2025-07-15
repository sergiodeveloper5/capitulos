from odoo import http
from odoo.http import request
import json

class CapitulosController(http.Controller):
    
    @http.route('/capitulos/add_product_to_section', type='json', auth='user')
    def add_product_to_section(self, order_id, chapter_name, section_name):
        """Endpoint para añadir un producto a una sección específica"""
        try:
            order = request.env['sale.order'].browse(order_id)
            if not order.exists():
                return {'error': 'Pedido no encontrado'}
            
            result = order.add_product_to_section(chapter_name, section_name)
            return {'success': True, 'result': result}
            
        except Exception as e:
            return {'error': str(e)}