from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    capitulo_ids = fields.Many2many(
        'capitulo.contrato', 
        string='Capítulos Aplicados',
        help="Capítulos técnicos aplicados a este pedido de venta"
    )
    
    capitulos_agrupados = fields.Text(
        string='Capítulos Agrupados',
        compute='_compute_capitulos_agrupados',
        help="JSON con las líneas agrupadas por capítulo para el widget acordeón"
    )
    
    tiene_multiples_capitulos = fields.Boolean(
        string='Mostrar Acordeón de Capítulos',
        compute='_compute_tiene_multiples_capitulos',
        help="Indica si el pedido tiene capítulos para mostrar en acordeón"
    )
    
    @api.depends('order_line', 'order_line.es_encabezado_capitulo', 'order_line.es_encabezado_seccion', 
                 'order_line.name', 'order_line.product_id', 'order_line.product_uom_qty', 
                 'order_line.product_uom', 'order_line.price_unit', 'order_line.price_subtotal', 'order_line.sequence')
    def _compute_capitulos_agrupados(self):
        """Agrupa las líneas del pedido por capítulos para mostrar en acordeón"""
        import json
        import logging
        _logger = logging.getLogger(__name__)
        
        for order in self:
            _logger.info(f"DEBUG COMPUTE: Procesando pedido {order.id} con {len(order.order_line)} líneas")
            
            capitulos_dict = {}
            current_capitulo_key = None
            current_seccion_name = None
            capitulo_counter = {}
            
            for line in order.order_line.sorted('sequence'):
                if line.es_encabezado_capitulo:
                    # Nuevo capítulo - crear clave única para permitir duplicados
                    base_name = line.name
                    if base_name not in capitulo_counter:
                        capitulo_counter[base_name] = 0
                    capitulo_counter[base_name] += 1
                    
                    # Crear clave única: nombre + contador si hay duplicados
                    if capitulo_counter[base_name] == 1:
                        current_capitulo_key = base_name
                    else:
                        current_capitulo_key = f"{base_name} ({capitulo_counter[base_name]})"
                    
                    capitulos_dict[current_capitulo_key] = {
                        'sections': {},
                        'total': 0.0
                    }
                    current_seccion_name = None
                    
                elif line.es_encabezado_seccion and current_capitulo_key:
                    # Nueva sección dentro del capítulo actual
                    current_seccion_name = line.name
                    capitulos_dict[current_capitulo_key]['sections'][current_seccion_name] = {
                        'lines': []
                    }
                    
                elif current_capitulo_key and current_seccion_name:
                    # Producto dentro de la sección actual
                    line_data = {
                        'id': line.id,  # Añadir ID para edición
                        'sequence': line.sequence,
                        'product_name': line.product_id.name if line.product_id else '',
                        'name': line.name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.name if line.product_uom else '',
                        'price_unit': line.price_unit,
                        'price_subtotal': line.price_subtotal
                    }
                    capitulos_dict[current_capitulo_key]['sections'][current_seccion_name]['lines'].append(line_data)
                    capitulos_dict[current_capitulo_key]['total'] += line.price_subtotal
            
            result_json = json.dumps(capitulos_dict) if capitulos_dict else '{}'
            order.capitulos_agrupados = result_json
            
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
        """Calcula si el pedido tiene capítulos para mostrar el acordeón"""
        for order in self:
            capitulos_count = len(order.order_line.filtered('es_encabezado_capitulo'))
            order.tiene_multiples_capitulos = capitulos_count >= 1
    
    def action_add_capitulo(self):
        """Acción para abrir el wizard de capítulos"""
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
        """Alterna el estado colapsado/expandido de un capítulo"""
        import json
        
        self.ensure_one()
        capitulos = json.loads(self.capitulos_agrupados or '[]')
        
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
        
        if not product_id:
            raise UserError("Debe seleccionar un producto")
        
        product = self.env['product.product'].browse(product_id)
        if not product.exists():
            raise UserError("El producto seleccionado no existe")
        
        _logger.info(f"DEBUG ADD_PRODUCT: Producto encontrado: {product.name}")
        
        # Buscar la línea de encabezado del capítulo
        capitulo_line = None
        seccion_line = None
        
        for line in order.order_line.sorted('sequence'):
            if line.es_encabezado_capitulo:
                # Comparar tanto el nombre exacto como el nombre base (sin contador)
                line_name = line.name
                # Extraer el nombre base si tiene formato "Nombre (contador)"
                import re
                base_name_match = re.match(r'^(.+?)(?:\s*\(\d+\))?$', capitulo_name)
                capitulo_base_name = base_name_match.group(1) if base_name_match else capitulo_name
                
                if line_name == capitulo_name or line_name == capitulo_base_name:
                    capitulo_line = line
                    _logger.info(f"DEBUG: Capítulo encontrado: {line.name}")
            elif capitulo_line and line.es_encabezado_seccion and line.name == seccion_name:
                seccion_line = line
                _logger.info(f"DEBUG: Sección encontrada: {line.name}")
                break
        
        if not capitulo_line:
            raise UserError(f"No se encontró el capítulo: {capitulo_name}")
        
        if not seccion_line:
            raise UserError(f"No se encontró la sección: {seccion_name} en el capítulo: {capitulo_name}")
        
        # Encontrar la posición donde insertar el nuevo producto
        # Debe ir inmediatamente después de la línea de sección
        
        # Buscar si ya hay productos en esta sección
        existing_products_in_section = []
        next_header_sequence = None
        
        # Buscar productos existentes en esta sección y el siguiente encabezado
        for line in order.order_line.filtered(lambda l: l.sequence > seccion_line.sequence).sorted('sequence'):
            if line.es_encabezado_capitulo or line.es_encabezado_seccion:
                next_header_sequence = line.sequence
                break
            else:
                # Es un producto en esta sección
                existing_products_in_section.append(line)
        
        _logger.info(f"DEBUG: Productos existentes en sección: {len(existing_products_in_section)}")
        _logger.info(f"DEBUG: Siguiente encabezado en secuencia: {next_header_sequence}")
        
        # Determinar la secuencia de inserción
        if existing_products_in_section:
            # Si ya hay productos, insertar después del último producto de la sección
            last_product_sequence = max(p.sequence for p in existing_products_in_section)
            insert_sequence = last_product_sequence + 1
            _logger.info(f"DEBUG: Insertando después del último producto en secuencia: {last_product_sequence}")
        else:
            # Si no hay productos, insertar inmediatamente después de la sección
            insert_sequence = seccion_line.sequence + 1
            _logger.info(f"DEBUG: Insertando inmediatamente después de la sección en secuencia: {seccion_line.sequence}")
        
        # Ajustar las secuencias de las líneas posteriores
        lines_to_update = order.order_line.filtered(
            lambda l: l.sequence >= insert_sequence
        )
        _logger.info(f"DEBUG: Actualizando secuencias de {len(lines_to_update)} líneas")
        
        for line in lines_to_update:
            old_sequence = line.sequence
            line.sequence += 1
            _logger.info(f"DEBUG: Línea '{line.name}' secuencia {old_sequence} -> {line.sequence}")
        
        _logger.info(f"DEBUG: Nueva línea se insertará en secuencia: {insert_sequence}")
        
        # Crear la nueva línea de producto
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
        
        # Crear la línea con contexto especial para evitar restricciones
        new_line = self.env['sale.order.line'].with_context(
            from_capitulo_wizard=True
        ).create(new_line_vals)
        
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
            raise
    
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
        # Si se está creando desde el wizard de capítulos, permitir la creación
        if self.env.context.get('from_capitulo_wizard'):
            return super().create(vals)
        
        # Bloquear la creación manual de encabezados de capítulos y secciones
        if vals.get('es_encabezado_capitulo') or vals.get('es_encabezado_seccion'):
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
                    raise UserError(
                        "No se pueden añadir secciones o notas manualmente cuando el presupuesto tiene capítulos estructurados.\n"
                        "Use el botón 'Gestionar Capítulos' para gestionar la estructura."
                    )
        
        return super().create(vals)