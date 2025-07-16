#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la adición de productos a secciones específicas
y identificar el problema que está causando el error RPC.
"""

import logging
logging.basicConfig(level=logging.INFO)

def test_add_product_to_section():
    """
    Prueba la adición de un producto a una sección específica
    """
    print("=== INICIANDO PRUEBA DE ADICIÓN DE PRODUCTO ===")
    
    # Obtener el entorno de Odoo
    try:
        # Buscar un pedido que tenga capítulos
        orders = env['sale.order'].search([
            ('order_line.es_encabezado_capitulo', '=', True)
        ], limit=1)
        
        if not orders:
            print("❌ No se encontraron pedidos con capítulos")
            return False
            
        order = orders[0]
        print(f"✅ Usando pedido: {order.name} (ID: {order.id})")
        
        # Mostrar estructura actual
        print("\n=== ESTRUCTURA ACTUAL ===")
        for line in order.order_line.sorted('sequence'):
            tipo = "CAPÍTULO" if line.es_encabezado_capitulo else "SECCIÓN" if line.es_encabezado_seccion else "PRODUCTO"
            print(f"  {line.sequence:3d}: [{tipo:8s}] {line.name}")
        
        # Buscar capítulos y secciones disponibles
        capitulos = order.order_line.filtered('es_encabezado_capitulo')
        secciones = order.order_line.filtered('es_encabezado_seccion')
        
        print(f"\n=== CAPÍTULOS DISPONIBLES ({len(capitulos)}) ===")
        for cap in capitulos:
            print(f"  - '{cap.name}'")
            
        print(f"\n=== SECCIONES DISPONIBLES ({len(secciones)}) ===")
        for sec in secciones:
            print(f"  - '{sec.name}'")
        
        # Buscar un producto para añadir
        products = env['product.product'].search([('sale_ok', '=', True)], limit=1)
        if not products:
            print("❌ No se encontraron productos")
            return False
            
        product = products[0]
        print(f"\n✅ Producto a añadir: {product.name} (ID: {product.id})")
        
        # Intentar añadir a la primera sección disponible
        if not secciones:
            print("❌ No hay secciones disponibles")
            return False
            
        # Encontrar el capítulo de la primera sección
        primera_seccion = secciones[0]
        capitulo_de_seccion = None
        
        for line in order.order_line.sorted('sequence'):
            if line.es_encabezado_capitulo:
                capitulo_de_seccion = line
            elif line.id == primera_seccion.id:
                break
                
        if not capitulo_de_seccion:
            print("❌ No se pudo encontrar el capítulo de la sección")
            return False
            
        print(f"\n=== INTENTANDO AÑADIR PRODUCTO ===")
        print(f"Capítulo: '{capitulo_de_seccion.name}'")
        print(f"Sección: '{primera_seccion.name}'")
        print(f"Producto: '{product.name}' (ID: {product.id})")
        
        # Llamar al método add_product_to_section
        try:
            result = env['sale.order'].add_product_to_section(
                order_id=order.id,
                capitulo_name=capitulo_de_seccion.name,
                seccion_name=primera_seccion.name,
                product_id=product.id,
                quantity=1.0
            )
            
            print(f"\n✅ ÉXITO: {result}")
            
            # Verificar la estructura después
            order.invalidate_recordset()
            print("\n=== ESTRUCTURA DESPUÉS ===")
            for line in order.order_line.sorted('sequence'):
                tipo = "CAPÍTULO" if line.es_encabezado_capitulo else "SECCIÓN" if line.es_encabezado_seccion else "PRODUCTO"
                print(f"  {line.sequence:3d}: [{tipo:8s}] {line.name}")
                
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            print(f"\nTraceback completo:")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_product_validation():
    """
    Prueba específica de validación de productos
    """
    print("\n=== PRUEBA DE VALIDACIÓN DE PRODUCTOS ===")
    
    try:
        # Buscar productos
        products = env['product.product'].search([('sale_ok', '=', True)], limit=5)
        print(f"Productos encontrados: {len(products)}")
        
        for product in products:
            print(f"  - {product.name} (ID: {product.id}) - UoM: {product.uom_id.name if product.uom_id else 'N/A'}")
            print(f"    Precio: {product.list_price} - Vendible: {product.sale_ok}")
            
        return len(products) > 0
        
    except Exception as e:
        print(f"❌ Error en validación de productos: {str(e)}")
        return False

def main():
    """
    Función principal de prueba
    """
    print("SCRIPT DE PRUEBA - ADICIÓN DE PRODUCTOS A SECCIONES")
    print("=" * 60)
    
    # Verificar que estamos en el entorno correcto
    try:
        if 'env' not in globals():
            print("❌ Este script debe ejecutarse en la consola de Odoo")
            print("Ejecute: python -c \"exec(open('test_add_product.py').read())\"")
            return False
            
        print(f"✅ Entorno Odoo disponible")
        print(f"Base de datos: {env.cr.dbname}")
        
        # Ejecutar pruebas
        if not test_product_validation():
            return False
            
        if not test_add_product_to_section():
            return False
            
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        return True
        
    except Exception as e:
        print(f"❌ Error en main: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()