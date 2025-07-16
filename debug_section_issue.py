#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de depuración para identificar por qué los productos
se añaden a la sección incorrecta en el widget de capítulos.

Ejecute este script desde la consola de Odoo:
exec(open('/path/to/debug_section_issue.py').read())
"""

import json
import logging

# Configurar logging
_logger = logging.getLogger(__name__)

def debug_capitulos_structure(order_id):
    """
    Analiza la estructura de capítulos de un pedido específico
    """
    print("\n" + "="*60)
    print("DEPURACIÓN DE ESTRUCTURA DE CAPÍTULOS")
    print("="*60)
    
    # Obtener el pedido
    order = env['sale.order'].browse(order_id)
    if not order.exists():
        print(f"❌ ERROR: No se encontró el pedido con ID {order_id}")
        return
    
    print(f"📋 Pedido: {order.name} (ID: {order.id})")
    print(f"📊 Total de líneas: {len(order.order_line)}")
    print("\n" + "-"*40)
    print("ESTRUCTURA DE LÍNEAS:")
    print("-"*40)
    
    # Mostrar todas las líneas ordenadas por secuencia
    for line in order.order_line.sorted('sequence'):
        line_type = ""
        if line.es_encabezado_capitulo:
            line_type = "📁 CAPÍTULO"
        elif line.es_encabezado_seccion:
            line_type = "📂 SECCIÓN"
        else:
            line_type = "📦 PRODUCTO"
        
        print(f"{line.sequence:3d}: {line_type} - '{line.name}'")
    
    print("\n" + "-"*40)
    print("DATOS JSON PARSEADOS:")
    print("-"*40)
    
    # Forzar recálculo y mostrar JSON
    order._compute_capitulos_agrupados()
    
    try:
        capitulos_data = json.loads(order.capitulos_agrupados or '{}')
        if capitulos_data:
            for cap_name, cap_data in capitulos_data.items():
                print(f"\n📁 Capítulo: '{cap_name}'")
                print(f"   💰 Total: {cap_data.get('total', 0)}")
                
                sections = cap_data.get('sections', {})
                if sections:
                    for sec_name, sec_data in sections.items():
                        lines_count = len(sec_data.get('lines', []))
                        print(f"   📂 Sección: '{sec_name}' ({lines_count} productos)")
                        
                        # Mostrar productos en la sección
                        for line_data in sec_data.get('lines', []):
                            print(f"      📦 {line_data.get('name', 'Sin nombre')} (ID: {line_data.get('id', 'N/A')})")
                else:
                    print("   ⚠️  Sin secciones")
        else:
            print("❌ No hay datos de capítulos")
    except Exception as e:
        print(f"❌ Error al parsear JSON: {e}")
        print(f"📄 JSON crudo: {order.capitulos_agrupados}")

def test_add_product_simulation(order_id, capitulo_name, seccion_name, product_id):
    """
    Simula la adición de un producto para depurar el proceso
    """
    print("\n" + "="*60)
    print("SIMULACIÓN DE ADICIÓN DE PRODUCTO")
    print("="*60)
    
    print(f"📋 Pedido ID: {order_id}")
    print(f"📁 Capítulo objetivo: '{capitulo_name}'")
    print(f"📂 Sección objetivo: '{seccion_name}'")
    print(f"📦 Producto ID: {product_id}")
    
    # Mostrar estructura antes
    print("\n🔍 ESTRUCTURA ANTES:")
    debug_capitulos_structure(order_id)
    
    try:
        # Intentar añadir el producto
        print("\n🚀 EJECUTANDO ADICIÓN...")
        result = env['sale.order'].add_product_to_section(
            order_id, capitulo_name, seccion_name, product_id, 1.0
        )
        print(f"✅ Resultado: {result}")
        
        # Mostrar estructura después
        print("\n🔍 ESTRUCTURA DESPUÉS:")
        debug_capitulos_structure(order_id)
        
    except Exception as e:
        print(f"❌ ERROR durante la adición: {e}")
        import traceback
        traceback.print_exc()

def find_orders_with_capitulos():
    """
    Encuentra pedidos que tienen capítulos configurados
    """
    print("\n" + "="*60)
    print("BUSCANDO PEDIDOS CON CAPÍTULOS")
    print("="*60)
    
    orders = env['sale.order'].search([
        ('tiene_multiples_capitulos', '=', True)
    ], limit=10)
    
    if orders:
        print(f"📋 Encontrados {len(orders)} pedidos con capítulos:")
        for order in orders:
            print(f"   - {order.name} (ID: {order.id})")
        return orders.ids
    else:
        print("❌ No se encontraron pedidos con capítulos")
        return []

# Función principal de depuración
def main_debug():
    """
    Función principal para ejecutar la depuración
    """
    print("🔧 INICIANDO DEPURACIÓN DEL WIDGET DE CAPÍTULOS")
    
    # Buscar pedidos con capítulos
    order_ids = find_orders_with_capitulos()
    
    if order_ids:
        # Usar el primer pedido encontrado
        order_id = order_ids[0]
        print(f"\n🎯 Usando pedido ID: {order_id}")
        
        # Analizar estructura
        debug_capitulos_structure(order_id)
        
        # Buscar un producto para probar
        products = env['product.product'].search([('sale_ok', '=', True)], limit=1)
        if products:
            product_id = products[0].id
            print(f"\n🧪 Producto de prueba: {products[0].name} (ID: {product_id})")
            
            # Aquí puedes especificar el capítulo y sección que quieres probar
            # Ejemplo:
            # test_add_product_simulation(order_id, "ALQUILER", "SECCIÓN FIJA", product_id)
            
        else:
            print("❌ No se encontraron productos para probar")
    else:
        print("❌ No hay pedidos con capítulos para depurar")

# Ejecutar depuración
if __name__ == '__main__':
    main_debug()
else:
    print("📝 Script de depuración cargado. Ejecute main_debug() para iniciar.")
    print("📝 O use las funciones individuales:")
    print("   - debug_capitulos_structure(order_id)")
    print("   - test_add_product_simulation(order_id, cap_name, sec_name, product_id)")
    print("   - find_orders_with_capitulos()")