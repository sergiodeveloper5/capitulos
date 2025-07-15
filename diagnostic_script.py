#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para el módulo de capítulos de Odoo 18.

Este script verifica:
1. Estructura de archivos del módulo
2. Sintaxis de archivos JavaScript y Python
3. Configuración del manifest
4. Métodos requeridos en los modelos
5. Compatibilidad con Odoo 18

Uso: python diagnostic_script.py
"""

import os
import json
import re
import ast

def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    """Imprime un título de sección"""
    print(f"\n📋 {title}:")
    print("-" * 40)

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✓ {description}: {os.path.basename(filepath)} ({size} bytes)")
        return True
    else:
        print(f"✗ {description}: {os.path.basename(filepath)} - NO ENCONTRADO")
        return False

def check_python_syntax(filepath):
    """Verifica la sintaxis de un archivo Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"✓ Sintaxis Python válida: {os.path.basename(filepath)}")
        return True
    except SyntaxError as e:
        print(f"✗ Error de sintaxis en {os.path.basename(filepath)}: {e}")
        return False
    except Exception as e:
        print(f"⚠ Error leyendo {os.path.basename(filepath)}: {e}")
        return False

def check_javascript_basic(filepath):
    """Verificación básica de JavaScript"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificaciones básicas
        checks = {
            'Importaciones Odoo': '@odoo-module' in content,
            'Registro del widget': 'registry.category("fields").add' in content,
            'Clase del componente': 'class CapitulosAccordionWidget' in content,
            'Método setup': 'setup()' in content,
            'Servicios ORM': 'useService("orm")' in content,
            'Método addProductToSection': 'addProductToSection' in content
        }
        
        all_good = True
        for check, result in checks.items():
            if result:
                print(f"✓ {check}")
            else:
                print(f"✗ {check}")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"✗ Error verificando JavaScript: {e}")
        return False

def check_xml_basic(filepath):
    """Verificación básica de XML"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'Declaración XML': '<?xml version="1.0"' in content,
            'Template principal': 'capitulos.CapitulosAccordionWidget' in content,
            'Botón Add Product': 'addProductToSection' in content,
            'Estructura de acordeón': 'accordion' in content
        }
        
        all_good = True
        for check, result in checks.items():
            if result:
                print(f"✓ {check}")
            else:
                print(f"✗ {check}")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"✗ Error verificando XML: {e}")
        return False

def check_method_in_file(filepath, method_name, class_name=None):
    """Verifica si un método existe en un archivo Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if class_name:
            pattern = rf'class\s+{class_name}.*?def\s+{method_name}'
        else:
            pattern = rf'def\s+{method_name}'
        
        if re.search(pattern, content, re.DOTALL):
            print(f"✓ Método {method_name} encontrado")
            return True
        else:
            print(f"✗ Método {method_name} NO encontrado")
            return False
    except Exception as e:
        print(f"✗ Error verificando método {method_name}: {e}")
        return False

def check_manifest_config(filepath):
    """Verifica la configuración del manifest"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Evaluar el diccionario del manifest
        manifest = eval(content)
        
        checks = {
            'Versión Odoo 18': manifest.get('version', '').startswith('18.'),
            'Dependencias básicas': 'sale_management' in manifest.get('depends', []),
            'Assets backend': 'web.assets_backend' in manifest.get('assets', {}),
            'JavaScript incluido': any('capitulos_accordion_widget.js' in asset 
                                    for asset in manifest.get('assets', {}).get('web.assets_backend', [])),
            'XML incluido': any('capitulos_accordion_templates.xml' in asset 
                              for asset in manifest.get('assets', {}).get('web.assets_backend', [])),
            'CSS incluido': any('capitulos_accordion.css' in asset 
                              for asset in manifest.get('assets', {}).get('web.assets_backend', []))
        }
        
        all_good = True
        for check, result in checks.items():
            if result:
                print(f"✓ {check}")
            else:
                print(f"✗ {check}")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"✗ Error verificando manifest: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    print_header("DIAGNÓSTICO DEL MÓDULO CAPÍTULOS - ODOO 18")
    
    base_path = "c:\\Users\\sergi\\Desktop\\capitulos"
    
    if not os.path.exists(base_path):
        print(f"✗ ERROR: No se encuentra el directorio del módulo: {base_path}")
        return
    
    print(f"📁 Directorio base: {base_path}")
    
    # 1. Verificar estructura de archivos
    print_section("1. ESTRUCTURA DE ARCHIVOS")
    
    files_to_check = [
        (f"{base_path}\\__manifest__.py", "Manifest del módulo"),
        (f"{base_path}\\__init__.py", "Init principal"),
        (f"{base_path}\\models\\sale_order.py", "Modelo SaleOrder"),
        (f"{base_path}\\controllers\\main.py", "Controlador Web"),
        (f"{base_path}\\controllers\\__init__.py", "Init Controladores"),
        (f"{base_path}\\static\\src\\js\\capitulos_accordion_widget.js", "Widget JavaScript"),
        (f"{base_path}\\static\\src\\xml\\capitulos_accordion_templates.xml", "Templates XML"),
        (f"{base_path}\\static\\src\\css\\capitulos_accordion.css", "Estilos CSS")
    ]
    
    all_files_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_files_exist = False
    
    # 2. Verificar sintaxis de archivos Python
    print_section("2. SINTAXIS DE ARCHIVOS PYTHON")
    
    python_files = [
        f"{base_path}\\__manifest__.py",
        f"{base_path}\\__init__.py",
        f"{base_path}\\models\\sale_order.py",
        f"{base_path}\\controllers\\main.py",
        f"{base_path}\\controllers\\__init__.py"
    ]
    
    python_syntax_ok = True
    for filepath in python_files:
        if os.path.exists(filepath):
            if not check_python_syntax(filepath):
                python_syntax_ok = False
    
    # 3. Verificar configuración del manifest
    print_section("3. CONFIGURACIÓN DEL MANIFEST")
    
    manifest_path = f"{base_path}\\__manifest__.py"
    manifest_ok = False
    if os.path.exists(manifest_path):
        manifest_ok = check_manifest_config(manifest_path)
    
    # 4. Verificar métodos en sale_order.py
    print_section("4. MÉTODOS EN SALE ORDER")
    
    sale_order_path = f"{base_path}\\models\\sale_order.py"
    methods_ok = True
    if os.path.exists(sale_order_path):
        if not check_method_in_file(sale_order_path, "add_product_to_section", "SaleOrder"):
            methods_ok = False
    
    # 5. Verificar widget JavaScript
    print_section("5. WIDGET JAVASCRIPT")
    
    js_path = f"{base_path}\\static\\src\\js\\capitulos_accordion_widget.js"
    js_ok = False
    if os.path.exists(js_path):
        js_ok = check_javascript_basic(js_path)
    
    # 6. Verificar template XML
    print_section("6. TEMPLATE XML")
    
    xml_path = f"{base_path}\\static\\src\\xml\\capitulos_accordion_templates.xml"
    xml_ok = False
    if os.path.exists(xml_path):
        xml_ok = check_xml_basic(xml_path)
    
    # Resumen final
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    results = {
        "Estructura de archivos": all_files_exist,
        "Sintaxis Python": python_syntax_ok,
        "Configuración Manifest": manifest_ok,
        "Métodos del modelo": methods_ok,
        "Widget JavaScript": js_ok,
        "Template XML": xml_ok
    }
    
    all_ok = all(results.values())
    
    for check, result in results.items():
        status = "✓ CORRECTO" if result else "✗ PROBLEMA"
        print(f"{status}: {check}")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 DIAGNÓSTICO COMPLETO: Todo parece estar correcto")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Reiniciar el servidor de Odoo")
        print("2. Actualizar el módulo desde Aplicaciones")
        print("3. Limpiar cache del navegador")
        print("4. Probar la funcionalidad")
    else:
        print("⚠️  DIAGNÓSTICO: Se encontraron problemas")
        print("\n📋 ACCIONES RECOMENDADAS:")
        print("1. Revisar los elementos marcados con ✗")
        print("2. Consultar TROUBLESHOOTING.md")
        print("3. Verificar logs de Odoo")
    
    print("\n📄 Para más información, consulte TROUBLESHOOTING.md")
    print("=" * 60)

if __name__ == "__main__":
    main()