# Guía de Instalación Rápida

## Pasos para Instalar el Módulo

### 1. Preparación
```bash
# Copiar el módulo a la carpeta de addons de Odoo
cp -r capitulos /path/to/odoo/addons/

# O crear un enlace simbólico
ln -s /path/to/capitulos /path/to/odoo/addons/capitulos
```

### 2. Instalación en Odoo

1. **Reiniciar Odoo** (si es necesario)
2. **Ir a Aplicaciones**
3. **Actualizar Lista de Aplicaciones**
4. **Buscar "Capítulos de Andamios"**
5. **Instalar el módulo**

### 3. Configuración de Usuarios

#### Asignar Permisos de Administrador
1. Ir a **Configuración > Usuarios y Compañías > Usuarios**
2. Seleccionar usuario administrador
3. En la pestaña **Derechos de Acceso**
4. Añadir grupo: **Administrador de Capítulos**

#### Asignar Permisos de Comercial
1. Seleccionar usuarios comerciales
2. Añadir grupo: **Comercial de Capítulos**

### 4. Verificación

1. **Ir a Ventas > Presupuestos**
2. **Crear o abrir un presupuesto**
3. **Verificar que aparecen los botones**:
   - "Crear Capítulo"
   - "Usar Plantilla"

### 5. Primer Uso

1. **Probar creación de capítulo**:
   - Clic en "Crear Capítulo"
   - Nombre: "Prueba"
   - Descripción: "Capítulo de prueba"
   - Confirmar

2. **Probar plantilla**:
   - Clic en "Usar Plantilla"
   - Seleccionar "MONTACARGAS MC-1700"
   - Confirmar

## Solución de Problemas

### Error: Módulo no aparece
- Verificar que está en la carpeta correcta de addons
- Reiniciar Odoo
- Actualizar lista de aplicaciones

### Error: Permisos insuficientes
- Verificar asignación de grupos de usuario
- Comprobar que el usuario tiene permisos de ventas

### Error: Vistas no cargan
- Verificar logs de Odoo
- Comprobar sintaxis XML en archivos de vistas
- Actualizar el módulo si es necesario

## Comandos Útiles

```bash
# Actualizar módulo (modo desarrollo)
./odoo-bin -u capitulos -d nombre_base_datos

# Instalar módulo desde línea de comandos
./odoo-bin -i capitulos -d nombre_base_datos

# Ver logs en tiempo real
tail -f /var/log/odoo/odoo.log
```

## Contacto

Para soporte técnico, contactar con el equipo de desarrollo de Sermaco.