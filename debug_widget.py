#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para el widget de capítulos
Este script ayuda a identificar problemas en la visualización de productos
"""

import json
import logging
from odoo import api, SUPERUSER_ID

def debug_widget_data(env, order_id):
    """Función para debuggear los datos del widget"""
    
    print("=" * 60)
    print("DIAGNÓSTICO DEL WIDGET DE CAPÍTULOS")
    print("=" * 60)
    
    # Obtener el pedido
    order = env['sale.order'].browse(order_id)
    if not order.exists():
        print(f"❌ ERROR: Pedido {order_id} no encontrado")
        return
    
    print(f"📋 Pedido: {order.name} (ID: {order.id})")
    print(f"📊 Estado: {order.state}")
    print(f"👤 Cliente: {order.partner_id.name}")
    print()
    
    # Verificar líneas del pedido
    print("📝 LÍNEAS DEL PEDIDO:")
    print("-" * 40)
    
    if not order.order_line:
        print("❌ No hay líneas en el pedido")
        return
    
    for i, line in enumerate(order.order_line.sorted('sequence'), 1):
        print(f"{i:2d}. ID:{line.id:4d} | Seq:{line.sequence:3d} | {line.name[:50]:<50} | Cap:{line.es_encabezado_capitulo} | Sec:{line.es_encabezado_seccion}")
    
    print()
    
    # Verificar campo computed
    print("🔄 CAMPO COMPUTED 'capitulos_agrupados':")
    print("-" * 40)
    
    # Forzar recálculo
    order._compute_capitulos_agrupados()
    
    capitulos_data = order.capitulos_agrupados
    print(f"📏 Longitud del JSON: {len(capitulos_data)} caracteres")
    
    if not capitulos_data or capitulos_data == '{}':
        print("❌ El campo capitulos_agrupados está vacío")
        return
    
    try:
        parsed_data = json.loads(capitulos_data)
        print(f"✅ JSON válido con {len(parsed_data)} capítulos")
        print()
        
        # Mostrar estructura de capítulos
        print("📂 ESTRUCTURA DE CAPÍTULOS:")
        print("-" * 40)
        
        for cap_name, cap_data in parsed_data.items():
            print(f"📁 Capítulo: {cap_name}")
            print(f"   💰 Total: {cap_data.get('total', 0)}")
            
            sections = cap_data.get('sections', {})
            print(f"   📑 Secciones: {len(sections)}")
            
            for sec_name, sec_data in sections.items():
                lines = sec_data.get('lines', [])
                print(f"      📄 {sec_name}: {len(lines)} productos")
                
                for j, line in enumerate(lines, 1):
                    print(f"         {j}. ID:{line.get('id', 'N/A')} | {line.get('name', 'Sin nombre')[:30]} | Qty:{line.get('product_uom_qty', 0)} | Price:{line.get('price_unit', 0)}")
            print()
            
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: JSON inválido - {e}")
        print(f"📄 Contenido: {capitulos_data[:200]}...")
        return
    
    # Verificar campo tiene_multiples_capitulos
    print("🔢 CAMPO 'tiene_multiples_capitulos':")
    print("-" * 40)
    print(f"✅ Valor: {order.tiene_multiples_capitulos}")
    
    # Contar encabezados
    capitulos_count = len(order.order_line.filtered('es_encabezado_capitulo'))
    print(f"📊 Encabezados de capítulo encontrados: {capitulos_count}")
    print()
    
    # Verificar dependencias del campo computed
    print("🔗 DEPENDENCIAS DEL CAMPO COMPUTED:")
    print("-" * 40)
    depends_fields = [
        'order_line', 'order_line.es_encabezado_capitulo', 'order_line.es_encabezado_seccion',
        'order_line.name', 'order_line.product_id', 'order_line.product_uom_qty',
        'order_line.product_uom', 'order_line.price_unit', 'order_line.price_subtotal', 'order_line.sequence'
    ]
    
    for field in depends_fields:
        print(f"   ✅ {field}")
    
    print()
    print("=" * 60)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 60)

def main():
    """Función principal para ejecutar el diagnóstico"""
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Obtener el entorno de Odoo
    # NOTA: Este script debe ejecutarse desde el contexto de Odoo
    # Por ejemplo: python3 -c "exec(open('debug_widget.py').read())" desde el shell de Odoo
    
    print("Para usar este script:")
    print("1. Abrir el shell de Odoo")
    print("2. Ejecutar: exec(open('debug_widget.py').read())")
    print("3. Luego ejecutar: debug_widget_data(env, ORDER_ID)")
    print("   donde ORDER_ID es el ID del pedido a diagnosticar")
    print()
    print("Ejemplo:")
    print("debug_widget_data(env, 1)  # Para diagnosticar el pedido con ID 1")

if __name__ == '__main__':
    main()