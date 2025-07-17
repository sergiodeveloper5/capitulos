# Módulo de Capítulos Técnicos para Odoo

## 📋 Descripción General

El **Módulo de Capítulos Técnicos** es una extensión avanzada para Odoo que permite organizar presupuestos y pedidos de venta en una estructura jerárquica de capítulos y secciones técnicas. Este módulo está especialmente diseñado para empresas que manejan proyectos complejos con múltiples fases y tipos de servicios.

## 🎯 Características Principales

### ✨ Gestión de Capítulos Técnicos
- **Estructura Jerárquica**: Organización de presupuestos en capítulos y secciones
- **Sistema de Plantillas**: Reutilización de capítulos predefinidos
- **Gestión de Dependencias**: Control de plantillas y sus dependencias
- **Wizard Intuitivo**: Interfaz amigable para creación y gestión

### 🔧 Tipos de Sección Especializados
- **Alquiler**: Productos y servicios de alquiler
- **Montaje**: Servicios de instalación y montaje
- **Desmontaje**: Servicios de desmontaje y retirada
- **Portes**: Servicios de transporte y logística
- **Otros**: Servicios adicionales y personalizados

### 📊 Visualización Avanzada
- **Vista Acordeón**: Navegación intuitiva por capítulos
- **Vista Tradicional**: Compatibilidad con vista estándar
- **Indicadores Visuales**: Estados y tipos claramente identificados
- **Búsqueda Avanzada**: Filtros especializados por tipo y capítulo

## 🏗️ Arquitectura del Módulo

### 📁 Estructura de Archivos

```
capitulos/
├── __init__.py                 # Inicialización del módulo
├── __manifest__.py            # Manifiesto y configuración
├── models/                    # Modelos de datos
│   ├── __init__.py
│   ├── capitulo_contrato.py   # Modelo principal de capítulos
│   ├── capitulo_seccion.py    # Modelo de secciones
│   ├── capitulo_wizard.py     # Wizard de gestión
│   ├── product_template.py    # Extensión de productos
│   └── sale_order.py          # Extensión de pedidos
├── views/                     # Vistas XML
│   ├── capitulo_views.xml     # Vistas de capítulos
│   ├── capitulo_wizard_view.xml # Vista del wizard
│   ├── product_views.xml      # Vistas de productos
│   └── sale_order_views.xml   # Vistas de pedidos
├── security/                  # Configuración de seguridad
│   └── ir.model.access.csv    # Permisos de acceso
└── README.md                  # Documentación
```

### 🗄️ Modelos de Datos

#### 1. **capitulo.contrato** - Capítulos Técnicos
- **Propósito**: Gestión de capítulos y plantillas
- **Características**: 
  - Sistema de plantillas reutilizables
  - Gestión de dependencias
  - Secciones organizadas por tipo
  - Condiciones legales personalizables

#### 2. **capitulo.seccion** - Secciones de Capítulo
- **Propósito**: Organización de productos por tipo de servicio
- **Características**:
  - Clasificación por tipo (alquiler, montaje, etc.)
  - Secuenciación automática
  - Productos con precios personalizables
  - Marcado de productos opcionales

#### 3. **capitulo.wizard** - Wizard de Gestión
- **Propósito**: Interfaz para añadir capítulos a presupuestos
- **Características**:
  - Modo existente/nuevo capítulo
  - Validaciones automáticas
  - Gestión de secciones dinámicas
  - Integración con pedidos de venta

#### 4. **Extensiones de Modelos Existentes**
- **product.template**: Clasificación por capítulo y tipo
- **sale.order**: Integración con estructura de capítulos
- **sale.order.line**: Soporte para jerarquía de capítulos

## 🚀 Funcionalidades Detalladas

### 📝 Gestión de Capítulos

#### Creación de Capítulos
- **Desde Cero**: Creación manual con secciones personalizadas
- **Desde Plantilla**: Reutilización de estructuras predefinidas
- **Clonación**: Duplicación de capítulos existentes

#### Sistema de Plantillas
- **Plantillas Base**: Estructuras reutilizables
- **Gestión de Dependencias**: Control de uso y eliminación
- **Actualización Automática**: Sincronización de cambios

### 🎛️ Wizard de Gestión

#### Modos de Operación
1. **Modo Existente**: Selección de capítulo predefinido
2. **Modo Nuevo**: Creación de capítulo personalizado

#### Funcionalidades del Wizard
- **Validación de Datos**: Verificación automática de integridad
- **Gestión de Secciones**: Añadir/editar secciones dinámicamente
- **Previsualización**: Vista previa antes de aplicar cambios
- **Múltiples Capítulos**: Añadir varios capítulos consecutivamente

### 📊 Visualización en Presupuestos

#### Vista Acordeón
- **Navegación Jerárquica**: Expansión/colapso de capítulos
- **Indicadores Visuales**: Estados y tipos claramente marcados
- **Acciones Rápidas**: Edición directa desde la vista
- **Totales Automáticos**: Cálculo dinámico de subtotales

#### Vista Tradicional
- **Compatibilidad**: Mantenimiento de funcionalidad estándar
- **Transición Suave**: Cambio automático según estructura
- **Funcionalidad Completa**: Todas las características de Odoo

## 🔧 Instalación y Configuración

### Requisitos Previos
- Odoo 15.0 o superior
- Módulo `sale` instalado
- Módulo `product` instalado

### Pasos de Instalación

1. **Copiar Módulo**
   ```bash
   cp -r capitulos /path/to/odoo/addons/
   ```

2. **Actualizar Lista de Módulos**
   - Ir a Aplicaciones > Actualizar Lista de Aplicaciones

3. **Instalar Módulo**
   - Buscar "Capítulos Técnicos"
   - Hacer clic en "Instalar"

4. **Configurar Permisos**
   - Asignar grupo "Gestión de Capítulos" a usuarios

### Configuración Inicial

1. **Crear Plantillas Base**
   - Ir a Ventas > Configuración > Plantillas de Capítulos
   - Crear plantillas para tipos comunes de proyecto

2. **Configurar Productos**
   - Asignar productos a capítulos y tipos de sección
   - Configurar precios por tipo de servicio

3. **Personalizar Vistas**
   - Ajustar campos visibles según necesidades
   - Configurar filtros predeterminados

## 📖 Guía de Uso

### Creación de Presupuesto con Capítulos

1. **Crear Pedido de Venta**
   - Ir a Ventas > Pedidos > Crear

2. **Gestionar Capítulos**
   - Hacer clic en "Gestionar Capítulos"
   - Seleccionar modo (Existente/Nuevo)

3. **Configurar Secciones**
   - Añadir secciones por tipo de servicio
   - Seleccionar productos para cada sección
   - Ajustar cantidades y precios

4. **Añadir al Presupuesto**
   - Revisar configuración
   - Hacer clic en "Añadir al Presupuesto"

### Gestión de Plantillas

1. **Crear Plantilla**
   - Ir a Configuración > Plantillas de Capítulos
   - Crear nueva plantilla con estructura base

2. **Usar Plantilla**
   - En el wizard, seleccionar "Capítulo Existente"
   - Elegir plantilla deseada
   - Personalizar según proyecto específico

3. **Gestionar Dependencias**
   - Ver capítulos que usan la plantilla
   - Actualizar plantilla base
   - Eliminar con control de dependencias

## 🔍 Características Técnicas

### Seguridad
- **Control de Acceso**: Permisos granulares por modelo
- **Grupos de Usuario**: Separación de roles y responsabilidades
- **Validaciones**: Verificación de integridad de datos

### Rendimiento
- **Consultas Optimizadas**: Uso eficiente de ORM de Odoo
- **Carga Lazy**: Carga bajo demanda de datos relacionados
- **Caché Inteligente**: Optimización de consultas frecuentes

### Extensibilidad
- **API Limpia**: Métodos bien definidos para extensiones
- **Hooks Personalizables**: Puntos de extensión para funcionalidades adicionales
- **Compatibilidad**: Diseño compatible con otros módulos

## 🐛 Solución de Problemas

### Problemas Comunes

#### Error: "No se pueden añadir productos sin secciones"
- **Causa**: Intento de añadir capítulo sin secciones configuradas
- **Solución**: Añadir al menos una sección con productos

#### Error: "Plantilla en uso, no se puede eliminar"
- **Causa**: Intento de eliminar plantilla con dependencias
- **Solución**: Usar "Eliminar Forzado" o eliminar dependencias primero

#### Vista no se actualiza correctamente
- **Causa**: Caché del navegador o problemas de sincronización
- **Solución**: Refrescar página o limpiar caché

### Logs y Depuración

El módulo incluye logging detallado para facilitar la depuración:

```python
# Activar logging en configuración de Odoo
[logger_capitulos]
level = DEBUG
handlers = console
qualname = odoo.addons.capitulos
```

## 🤝 Contribución

### Reportar Problemas
- Usar el sistema de issues del repositorio
- Incluir información detallada del error
- Proporcionar pasos para reproducir

### Desarrollo
- Seguir estándares de código de Odoo
- Incluir tests para nuevas funcionalidades
- Documentar cambios en README

### Testing
```bash
# Ejecutar tests del módulo
python -m pytest tests/
```

## 📄 Licencia

Este módulo está licenciado bajo LGPL-3.0. Ver archivo LICENSE para más detalles.

## 📞 Soporte

Para soporte técnico y consultas:
- **Email**: soporte@empresa.com
- **Documentación**: [Wiki del proyecto]
- **Issues**: [GitHub Issues]

## 🔄 Changelog

### Versión 1.0.0
- ✅ Implementación inicial del módulo
- ✅ Sistema de capítulos y secciones
- ✅ Wizard de gestión
- ✅ Integración con pedidos de venta
- ✅ Sistema de plantillas
- ✅ Vistas especializadas

### Próximas Versiones
- 🔄 Reportes especializados
- 🔄 Integración con proyectos
- 🔄 API REST para integraciones
- 🔄 Importación/exportación de plantillas

---

**Desarrollado con ❤️ para optimizar la gestión de presupuestos técnicos en Odoo**