odoo.define('capitulos.CapitulosAccordionWidget', function (require) {
    'use strict';

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var CapitulosAccordionWidget = AbstractField.extend({
        className: 'o_capitulos_accordion',
        supportedFieldTypes: ['text'],
        
        init: function () {
            this._super.apply(this, arguments);
            this.collapsedChapters = new Set();
        },

        _render: function () {
            var self = this;
            var data = this.value ? JSON.parse(this.value) : {};
            
            this.$el.empty();
            
            if (!data || Object.keys(data).length === 0) {
                this.$el.html('<div class="alert alert-info">No hay capítulos para mostrar</div>');
                return;
            }

            var $accordion = $('<div class="accordion" id="capitulosAccordion"></div>');
            
            Object.keys(data).forEach(function(chapterName, index) {
                var chapter = data[chapterName];
                var chapterId = 'chapter_' + index;
                var isCollapsed = self.collapsedChapters.has(chapterName);
                
                var $card = $('<div class="card mb-2"></div>');
                
                // Header del capítulo
                var $header = $('<div class="card-header p-2" style="background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;"></div>');
                var $headerButton = $('<button class="btn btn-link text-left w-100 d-flex justify-content-between align-items-center" ' +
                    'type="button" data-toggle="collapse" data-target="#' + chapterId + '" ' +
                    'aria-expanded="' + (!isCollapsed) + '" aria-controls="' + chapterId + '" ' +
                    'style="text-decoration: none; color: #495057; font-weight: 500;">' +
                    '<span><i class="fa fa-folder-o mr-2"></i>' + chapterName + '</span>' +
                    '<i class="fa fa-chevron-' + (isCollapsed ? 'right' : 'down') + '"></i>' +
                    '</button>');
                
                $header.append($headerButton);
                $card.append($header);
                
                // Contenido del capítulo
                var $collapse = $('<div id="' + chapterId + '" class="collapse' + (isCollapsed ? '' : ' show') + '" data-parent="#capitulosAccordion"></div>');
                var $body = $('<div class="card-body p-0"></div>');
                
                // Tabla de líneas
                var $table = $('<table class="table table-sm mb-0"></table>');
                var $thead = $('<thead style="background-color: #e9ecef;"></thead>');
                var $headerRow = $('<tr></tr>');
                $headerRow.append('<th style="width: 40px;">Seq</th>');
                $headerRow.append('<th>Producto</th>');
                $headerRow.append('<th>Descripción</th>');
                $headerRow.append('<th style="width: 80px;">Cantidad</th>');
                $headerRow.append('<th style="width: 80px;">Unidad</th>');
                $headerRow.append('<th style="width: 100px;">Precio Unit.</th>');
                $headerRow.append('<th style="width: 100px;">Subtotal</th>');
                $thead.append($headerRow);
                $table.append($thead);
                
                var $tbody = $('<tbody></tbody>');
                
                // Agregar secciones y líneas
                Object.keys(chapter.sections).forEach(function(sectionName) {
                    var section = chapter.sections[sectionName];
                    
                    // Fila de sección
                    var $sectionRow = $('<tr style="background-color: #fff3cd; font-weight: 500;"></tr>');
                    $sectionRow.append('<td></td>');
                    $sectionRow.append('<td colspan="6"><i class="fa fa-tag mr-2"></i>' + sectionName + '</td>');
                    $tbody.append($sectionRow);
                    
                    // Líneas de la sección
                    section.lines.forEach(function(line) {
                        var $lineRow = $('<tr></tr>');
                        $lineRow.append('<td>' + (line.sequence || '') + '</td>');
                        $lineRow.append('<td>' + (line.product_name || '') + '</td>');
                        $lineRow.append('<td>' + (line.name || '') + '</td>');
                        $lineRow.append('<td class="text-right">' + (line.product_uom_qty || 0) + '</td>');
                        $lineRow.append('<td>' + (line.product_uom || '') + '</td>');
                        $lineRow.append('<td class="text-right">' + (line.price_unit || 0).toFixed(2) + '</td>');
                        $lineRow.append('<td class="text-right">' + (line.price_subtotal || 0).toFixed(2) + '</td>');
                        $tbody.append($lineRow);
                    });
                });
                
                // Fila de total del capítulo
                var $totalRow = $('<tr style="background-color: #d4edda; font-weight: bold;"></tr>');
                $totalRow.append('<td colspan="6" class="text-right">Total ' + chapterName + ':</td>');
                $totalRow.append('<td class="text-right">' + (chapter.total || 0).toFixed(2) + '</td>');
                $tbody.append($totalRow);
                
                $table.append($tbody);
                $body.append($table);
                $collapse.append($body);
                $card.append($collapse);
                $accordion.append($card);
                
                // Event listener para el colapso
                $headerButton.on('click', function() {
                    setTimeout(function() {
                        var isNowCollapsed = !$collapse.hasClass('show');
                        if (isNowCollapsed) {
                            self.collapsedChapters.add(chapterName);
                        } else {
                            self.collapsedChapters.delete(chapterName);
                        }
                        
                        // Actualizar icono
                        var $icon = $headerButton.find('i:last');
                        $icon.removeClass('fa-chevron-down fa-chevron-right');
                        $icon.addClass(isNowCollapsed ? 'fa-chevron-right' : 'fa-chevron-down');
                    }, 350); // Esperar a que termine la animación
                });
            });
            
            this.$el.append($accordion);
        },
    });

    fieldRegistry.add('capitulos_accordion', CapitulosAccordionWidget);

    return CapitulosAccordionWidget;
});