#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para diagnosticar problemas con el widget de capítulos

Este script debe ejecutarse desde la consola de Odoo o como un script independiente
que se conecte a la base de datos de Odoo.
"""

import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

def test_capitulos_widget():
    """
    Función de prueba para verificar el funcionamiento del widget de capítulos
    """
    print("=== INICIANDO PRUEBAS DEL WIDGET DE CAPÍTULOS ===")
    
    # Esta función debe ser llamada desde el contexto de Odoo
    # con acceso a self.env
    
    try:
        # Buscar un pedido de venta existente
        orders = self.env['sale.order'].search([('state', '=', 'draft')], limit=1)
        
        if not orders:
            print("❌ No se encontraron pedidos en borrador")
            return False
            
        order = orders[0]
        print(f"✅ Usando pedido: {order.name} (ID: {order.id})")
        
        # Verificar líneas existentes
        print(f"📋 Líneas existentes: {len(order.order_line)}")
        for line in order.order_line:
            print(f"  - {line.sequence}: {line.name} (Cap: {line.es_encabezado_capitulo}, Sec: {line.es_encabezado_seccion})")
        
        # Verificar campo computed
        print(f"🔄 Campo capitulos_agrupados: {len(order.capitulos_agrupados)} caracteres")
        print(f"🔄 Tiene múltiples capítulos: {order.tiene_multiples_capitulos}")
        
        # Intentar parsear el JSON
        try:
            data = json.loads(order.capitulos_agrupados or '{}')
            print(f"✅ JSON válido con {len(data)} capítulos")
            
            for cap_name, cap_data in data.items():
                sections = cap_data.get('sections', {})
                print(f"  📁 Capítulo '{cap_name}': {len(sections)} secciones")
                
                for sec_name, sec_data in sections.items():
                    lines = sec_data.get('lines', [])
                    print(f"    📂 Sección '{sec_name}': {len(lines)} productos")
                    
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            print(f"❌ Contenido: {order.capitulos_agrupados[:200]}...")
        
        # Forzar recálculo
        print("🔄 Forzando recálculo...")
        order._compute_capitulos_agrupados()
        order._compute_tiene_multiples_capitulos()
        
        print(f"🔄 Después del recálculo: {len(order.capitulos_agrupados)} caracteres")
        print(f"🔄 Tiene múltiples capítulos: {order.tiene_multiples_capitulos}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_add_product():
    """
    Prueba la adición de un producto a una sección
    """
    print("\n=== PROBANDO ADICIÓN DE PRODUCTO ===")
    
    try:
        # Buscar un pedido con capítulos
        orders = self.env['sale.order'].search([
            ('state', '=', 'draft'),
            ('tiene_multiples_capitulos', '=', True)
        ], limit=1)
        
        if not orders:
            print("❌ No se encontraron pedidos con capítulos")
            return False
            
        order = orders[0]
        print(f"✅ Usando pedido: {order.name} (ID: {order.id})")
        
        # Buscar un producto
        products = self.env['product.product'].search([('sale_ok', '=', True)], limit=1)
        if not products:
            print("❌ No se encontraron productos")
            return False
            
        product = products[0]
        print(f"✅ Usando producto: {product.name} (ID: {product.id})")
        
        # Buscar capítulos y secciones existentes
        capitulos_data = json.loads(order.capitulos_agrupados or '{}')
        
        if not capitulos_data:
            print("❌ No hay capítulos en el pedido")
            return False
            
        # Tomar el primer capítulo y primera sección
        cap_name = list(capitulos_data.keys())[0]
        cap_data = capitulos_data[cap_name]
        
        if not cap_data.get('sections'):
            print(f"❌ El capítulo '{cap_name}' no tiene secciones")
            return False
            
        sec_name = list(cap_data['sections'].keys())[0]
        
        print(f"🎯 Añadiendo producto a capítulo '{cap_name}', sección '{sec_name}'")
        
        # Contar líneas antes
        lines_before = len(order.order_line)
        
        # Añadir producto
        result = order.add_product_to_section(
            order.id, cap_name, sec_name, product.id, 1.0
        )
        
        print(f"📤 Resultado: {result}")
        
        # Verificar después
        order.invalidate_recordset()
        lines_after = len(order.order_line)
        
        print(f"📊 Líneas antes: {lines_before}, después: {lines_after}")
        
        if lines_after > lines_before:
            print("✅ Producto añadido correctamente")
            
            # Verificar que el campo computed se actualizó
            order._compute_capitulos_agrupados()
            new_data = json.loads(order.capitulos_agrupados or '{}')
            
            if cap_name in new_data and sec_name in new_data[cap_name].get('sections', {}):
                new_lines = new_data[cap_name]['sections'][sec_name].get('lines', [])
                print(f"✅ Sección ahora tiene {len(new_lines)} productos")
            else:
                print("❌ La sección no se encontró en los datos actualizados")
                
        else:
            print("❌ No se añadió ninguna línea")
            
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba de adición: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Este script debe ejecutarse desde el contexto de Odoo")
    print("Ejemplo de uso en la consola de Odoo:")
    print("")
    print("# Importar el script")
    print("exec(open('/path/to/test_debug.py').read())")
    print("")
    print("# Ejecutar las pruebas")
    print("test_capitulos_widget()")
    print("test_add_product()")