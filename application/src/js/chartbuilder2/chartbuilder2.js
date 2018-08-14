
/*
    Functionality of chartbuilder including the main methods that run each stage


    On open **initialiseForm()**
    - grab current_settings from dimension.chart_2_source_data if such a thing exists
    - if current_settings doesn't exist open with the data area open.
    - otherwise set the current_settings from file, paste data into the data panel and run the On new data routine below

    On new data (changing data in the data panel area and clicking Okay) **handleNewData()**
    - use an AJAX call to the /get-valid-presets-for-data endpoint to add extra values **buildDataWithPreset()**
    - populate the chart builder dropdowns with correct values **populateChartOptions(), populateEthnicityPresets()**
    - if any settings currently exist apply as many as are still relevant **setupChartbuilderWithSettings()**

    On settings changes
    - validate they will make a viable chart **getTips()**
    - if so use the rd chart object factory and renderer to display a preview **preview()**
    - otherwise display an error and tip to fix it **displayTips()**

    On save
    - build a chart object with the rd-chart-object factory **buildChartObject()**
    - create a chart_settings lump of json **getChartPageSettings()**
    - post both to <dimension>/create-chart endpoint **postChartObject()**
 */

// The main working data variables
var presets = [];
var chart_data = null;

// Variables that needs to be maintained when the user makes changes to the text data
var current_data = "";
var current_settings = null;

$(document).ready(function () {

    // add events to buttons
    $('#preview').click(preview);
    $('#confirm-data').click(setChartData);
    $('#edit-data').click(editChartData);
    $('#cancel-edit-data').click(cancelEditData);
    $('#save').click(saveChart);
    $('#exit').click(back);

    function back(evt) {
        window.location.replace(url_edit_dimension)
    }

    /*
    Events from the DATA ENTRY PANEL
    */
    function setChartData(evt) {
        handleNewData(function () {
            if (current_settings) {
                setupChartbuilderWithSettings(current_settings)
            }
            preview()
        });
        $('#data-panel').hide();
        $('#edit-panel').show();
    }

    function editChartData(evt) {
        current_data = $('#data_text_area').val();
        current_settings = getChartPageSettings();
        $('#data-panel').show();
        $('#edit-panel').hide();
    }

    function cancelEditData(evt) {
        $('#data_text_area').val(current_data);
        $('#data-panel').hide();
        $('#edit-panel').show();
    }


    /*
    Initialise the main editor after DATA ENTRY PANEL change
    */

    function handleNewData(on_success) {

        // get the data
        var tabbedData = $("#data_text_area").val();

        // set the DATA DISPLAY content
        chart_data = textToData(tabbedData);
        if (chart_data.length > 0) {
            message = chart_data.length - 1 + ' rows by ' + chart_data[0].length + ' columns'
        }
        $('#data-description').html(message);

        // update options in drop-downs
        var headers = chart_data[0];
        populateChartOptions(headers);

        // call the backend to do the presets heavy lifting
        var ethnicity_data = get_ethnicity_values(chart_data);
        $.ajax({
            type: "post",
            url: url_auto_data,
            dataType: 'json',
            data: JSON.stringify({ 'data': ethnicity_data }),
            contentType: 'application/json; charset=utf-8',
            success: function (response) {
                // upon heavy lifting complete

                // populate the ethnicity presets from the response
                presets = response['presets'];
                populateEthnicityPresets(presets);

                // show the presets (step 2) and chart type (step 3) section
                $('#ethnicity_settings_section').show();
                $('#select_chart_type').show();

                // any further processing
                if (on_success) {
                    on_success();
                }
            },
            failure: function () {
                console.log('failure');
            },
            error: function (err) {
                console.log(err);
            }
        });
    }

    function get_ethnicity_values(data) {
        var all_data = _.clone(data);
        var headers = all_data.shift();

        var column = get_ethnicity_column(headers);
        if (column >= 0) {
            return _.pluck(all_data, column);
        }
        return [];
    }

    function get_ethnicity_column(headers) {
        var ETHNICITY_COLUMNS = ['ethnicity', 'ethnic group']
        console.log(ETHNICITY_COLUMNS.indexOf('Ethnicity'.toLowerCase().trim()));
        for (var index = 0; index < headers.length; index++) {
            var headerLowerTrim = headers[index].toLowerCase().trim();
            if (ETHNICITY_COLUMNS.indexOf(headerLowerTrim) >= 0) {
                return index
            }
        }
        return -1;
    }


    /*
    SETUP
    */

    function populateChartOptions(headers) {
        var listWithNone = dropdownHtmlWithDefault(headers, '[None]');
        var listWithRequired = dropdownHtmlWithDefault(headers, '[Required]');

        $('#line__x-axis_column').html(listWithRequired);

        $('#grouped-bar__bar_column').html(listWithRequired);
        $('#grouped-bar__bar_order').html(listWithNone);
        $('#grouped-bar__groups_column').html(listWithRequired);
        $('#grouped-bar__groups_order').html(listWithNone);

        $('#component__bar_column').html(listWithRequired);
        $('#component__bar_order').html(listWithNone);
        $('#component__section_column').html(listWithRequired);
        $('#component__section_order').html(listWithNone);

        $('#panel-bar__panel_column').html(listWithRequired);
        $('#panel-bar__panel_order').html(listWithNone);
        $('#panel-bar__bar_column').html(listWithRequired);
        $('#panel-bar__bar_order').html(listWithNone);

        $('#panel-line__x-axis_column').html(listWithRequired);
    }

    function selectDropdown(dropdown_id, value) {
        var dropdown = document.getElementById(dropdown_id);
        for (var i = 0; i < dropdown.length; i++) {
            dropdown[i].selected = (dropdown[i].value === value)
        }
    }


    function populateEthnicityPresets(presets) {
        var html = '';
        for (var p in presets) {
            var preset = presets[p]['preset']['name'];
            var code = presets[p]['preset']['code'];
            if (p === 0) {
                html = html + '<option value="' + code + '" selected>' + preset + '</option>';
            } else {
                html = html + '<option value="' + code + '" >' + preset + '</option>';
            }
        }
        $('#ethnicity_settings').html(html);
    }

    function strippedHeaders(headers) {
        var exclude = ['Measure', 'Ethnicity', 'Ethnic group', 'Value', 'Values'];
        var stripped = [];
        for (h in headers) {
            var header = headers[h];
            if (exclude.indexOf(header) < 0) {
                stripped.push(header);
            }
        }
        return stripped;
    }

    function dropdownHtmlWithDefault(headers, defaultValue) {
        var html = '<option value="' + defaultValue + '" selected>' + defaultValue + '</option>';
        var stripped = strippedHeaders(headers);
        for (var h in stripped) {
            var header = stripped[h];
            html = html + '<option value="' + header + '">' + header + '</option>';
        }
        return html;
    }

    /*
    PREVIEW
    Render the chart as a preview using drawChart() from rd - graph.js (this the exact same method that is used front - end)
    */

    function preview(evt) {
        var tips = getTips();
        if (tips.length > 0) {
            displayTips(tips);
        } else {
            displayChart();
        }
    }

    function displayTips(tips) {
        $('#tips_container').show();
        $('#preview_container').hide();

        $("#notes_container").hide();
        $("#errors_container").hide();

        $("#tip-list").children().hide();

        if (tipsOfType(tips, MISSING_FIELD_ERROR).length > 0) {
            $("#notes_container").show();
        }
        if (tipsOfType(tips, ETHNICITY_ERROR).length > 0) {
            $("#errors_container").show();
            $('#tip__ethnicity-column').show();
        }
        if (tipsOfType(tips, VALUE_ERROR).length > 0) {
            $("#errors_container").show();
            $('#tip__value-column').show();
        }
        if (tipsOfType(tips, RECTANGLE_ERROR).length > 0) {
            $("#errors_container").show();
            $('#tip__rectangular-data').show();
        }
        if (tipsOfType(tips, DATA_ERROR_COMPLEX_DATA).length > 0) {
            $("#errors_container").show();
            $('#tip__complex-data').show();
        }
        if (tipsOfType(tips, DATA_ERROR_DUPLICATION).length > 0) {
            $("#errors_container").show();
            $('#tip__duplicate-data').show();
        }
        if (tipsOfType(tips, DATA_ERROR_MISSING_DATA).length > 0) {
            $("#errors_container").show();
            $('#tip__missing-data').show();
        }

    }

    function tipsOfType(tips, errorType) {
        return _.filter(tips, function (tip) {
            return tip.errorType === errorType;
        })
    }

    function displayChart() {
        $('#tips_container').hide();
        $('#preview_container').show();

        var chartObject = buildChartObject();
        if (chartObject) {
            if (chartObject.title && chartObject.title.text) {
                $('#title-container').html('<h3 class="heading-small">' + chartObject.title.text + '</h3>');
            }
            chartObject.title = '';
            drawChart('container', chartObject);

            $('#save_section').show();
        }
    }

    /*
    SAVE
    Save the chart by building a chartObject and bundling up all the setting then sending it to the backend
    */

    function saveChart(evt) {

        $('#save').attr('disabled', 'disabled');

        var chartObject = buildChartObject();
        var chartBuilderSettings = getChartPageSettings();
        if (chartObject) {
            postChartObject(chartObject, chartBuilderSettings);
        }
    }

    function postChartObject(chartObject, src) {
        if (chartObject) {
            // adjust for null data
            $.each(chartObject.series, function () {
                for (var i = 0; i < this.data.length; i++) {
                    if (isNaN(this.data[i].y)) {
                        this.data[i].y = 0;
                    }
                }
            });

            $.ajax({
                type: "POST",
                url: url_save_chart_to_page,
                dataType: 'json',
                data: JSON.stringify({ 'chartObject': chartObject, 'source': src, 'chartBuilderVersion': 2 }),
                contentType: 'application/json',
                success: function () {
                    location.reload();
                }
            });
        }
    }

    function getChartPageSettings() {
        // get the data
        var tabbedData = $("#data_text_area").val();
        var chartType = $('#chart_type_selector').val();
        return {
            'data': textToData(tabbedData),
            'type': chartType,
            'preset': getPresetCode(),
            'chartOptions': getChartTypeOptions(chartType),
            'chartFormat': getChartFormat(),
            'version': '2.0'
        }
    }

    function getChartTypeOptions(chartType) {
        switch (chartType) {
            case 'bar_chart':
                return {};
            case 'line_graph':
                return { 'x_axis_column': $('#line__x-axis_column').val() };
            case 'grouped_bar_chart':
                var dataStyle = $('#grouped-bar__data_style').val();
                if (dataStyle === 'ethnicity_as_group') {
                    return { 'data_style': dataStyle, 'bar_column': $('#grouped-bar__bar_column').val() }
                } else {
                    return { 'data_style': dataStyle, 'group_column': $('#grouped-bar__groups_column').val() }
                }
            case 'component_chart':
                var dataStyle = $('#component__data_style').val();
                if (dataStyle === 'ethnicity_as_sections') {
                    return {
                        'data_style': dataStyle, 'bar_column': $('#component__bar_column').val(),
                        'bar_order': $('#component__bar_order').val()
                    }
                } else {
                    return {
                        'data_style': dataStyle, 'section_column': $('#component__section_column').val(),
                        'section_order': $('#component__section_order').val()
                    }
                }
            case 'panel_bar_chart':
                var dataStyle = $('#panel-bar__data_style').val();
                if (dataStyle === 'ethnicity_as_panels') {
                    return {
                        'data_style': dataStyle, 'bar_column': $('#panel-bar__bar_column').val(),
                        'bar_order': $('#panel-bar__bar_order').val()
                    }
                } else {
                    return {
                        'data_style': dataStyle, 'panel_column': $('#panel-bar__panel_column').val(),
                        'panel_order': $('#panel-bar__panel_order').val()
                    }
                }
            case 'panel_line_chart':
                return { 'x_axis_column': $('#panel-line__x-axis_column').val() };
            default:
                return {};
        }
    }

    function getChartFormat() {
        return {
            'chart_title': $('#chart_title').val(),
            'x_axis_label': $('#x_axis_label').val(),
            'y_axis_label': $('#y_axis_label').val(),
            'number_format': $('#number_format').val(),
            'number_format_prefix': $('#number_format_prefix').val(),
            'number_format_suffix': $('#number_format_suffix').val(),
            'number_format_min': $('#number_format_min').val(),
            'number_format_max': $('#number_format_max').val()
        }
    }

    function getPresetCode() {
        return $('#ethnicity_settings').val();
    }


    function buildChartObject() {
        var chart_type = $('#chart_type_selector').val();
        var chartObject = null;
        var preset = getPresetWithCode($('#ethnicity_settings').val());
        if (chart_type === 'bar_chart') {
            chartObject = barchartObject(buildDataWithPreset(preset, chart_data, ['value']),
                'Ethnicity',
                '[None]',
                'Ethnicity-parent',
                'Ethnicity-order',
                $('#chart_title').val(),
                $('#x_axis_label').val(),
                $('#y_axis_label').val(),
                getNumberFormat());
        } else if (chart_type === 'line_graph') {
            var x_axis_column = $('#line__x-axis_column').val();
            chartObject = linechartObject(buildDataWithPreset(preset, chart_data, ['value', x_axis_column]),
                x_axis_column,
                'Ethnicity',
                $('#chart_title').val(),
                $('#x_axis_label').val(),
                $('#y_axis_label').val(),
                getNumberFormat(),
                'Ethnicity-order');
        } else if (chart_type === 'grouped_bar_chart') {
            if ($('#grouped-bar__data_style').val() === 'ethnicity_as_group') {
                var barColumn = $('#grouped-bar__bar_column').val();
                chartObject = barchartObject(buildDataWithPreset(preset, chart_data, ['value', barColumn]),
                    'Ethnicity',
                    barColumn,
                    '[None]',
                    'Ethnicity-order',
                    $('#chart_title').val(),
                    $('#x_axis_label').val(),
                    $('#y_axis_label').val(),
                    getNumberFormat());
            } else {
                var groupColumn = $('#grouped-bar__groups_column').val();
                chartObject = barchartObject(buildDataWithPreset(preset, chart_data, ['value', groupColumn]),
                    groupColumn,
                    'Ethnicity',
                    '[None]',
                    'Ethnicity-order',
                    $('#chart_title').val(),
                    $('#x_axis_label').val(),
                    $('#y_axis_label').val(),
                    getNumberFormat());
            }
        } else if (chart_type === 'component_chart') {
            if ($('#component__data_style').val() === 'ethnicity_as_bar') {
                var sectionColumn = $('#component__section_column').val();
                var sectionOrder = $('#component__section_order').val();
                var data = [];
                if (sectionOrder && sectionOrder !== '[None]') {
                    data = buildDataWithPreset(preset, chart_data, ['value', sectionColumn, sectionOrder])
                } else {
                    data = buildDataWithPreset(preset, chart_data, ['value', sectionColumn])
                }
                chartObject = componentChartObject(data,
                    'Ethnicity',
                    sectionColumn,
                    $('#chart_title').val(),
                    $('#x_axis_label').val(),
                    $('#y_axis_label').val(),
                    getNumberFormat(),
                    'Ethnicity-order',
                    sectionOrder)
            } else {
                var groupColumn = $('#component__bar_column').val();
                var groupOrder = $('#component__bar_order').val();
                var data = [];
                if (groupOrder && groupOrder !== '[None]') {
                    data = buildDataWithPreset(preset, chart_data, ['value', groupColumn, groupOrder])
                } else {
                    data = buildDataWithPreset(preset, chart_data, ['value', groupColumn])
                }
                chartObject = componentChartObject(buildDataWithPreset(preset, chart_data, ['value', groupColumn]),
                    groupColumn,
                    'Ethnicity',
                    $('#chart_title').val(),
                    $('#x_axis_label').val(),
                    $('#y_axis_label').val(),
                    getNumberFormat(),
                    groupOrder,
                    'Ethnicity-order')
            }
        } else if (chart_type === 'panel_bar_chart') {
            if ($('#panel-bar__data_style').val() === 'ethnicity_as_panel_bars') {
                var panelColumn = $('#panel-bar__panel_column').val();
                var panelOrder = $('#panel-bar__panel_order').val();
                var data = [];
                if (panelOrder && panelOrder !== '[None]') {
                    data = buildDataWithPreset(preset, chart_data, ['value', panelColumn, panelOrder])
                } else {
                    data = buildDataWithPreset(preset, chart_data, ['value', panelColumn])
                }
                chartObject = panelBarchartObject(data,
                    'Ethnicity',
                    panelColumn,
                    $('#chart_title').val(),
                    '',
                    '',
                    getNumberFormat(),
                    'Ethnicity-order',
                    panelOrder)
            } else {
                var panelBarColumn = $('#panel-bar__bar_column').val();
                var panelBarOrder = $('#panel-bar__bar_order').val();
                var data = [];
                if (panelBarColumn && panelBarOrder !== '[None]') {
                    data = buildDataWithPreset(preset, chart_data, ['value', panelBarColumn, panelBarOrder])
                } else {
                    data = buildDataWithPreset(preset, chart_data, ['value', panelBarColumn])
                }
                chartObject = panelBarchartObject(data,
                    panelBarColumn,
                    'Ethnicity',
                    $('#chart_title').val(),
                    '',
                    '',
                    getNumberFormat(),
                    panelBarOrder,
                    'Ethnicity-order')
            }
        } else if (chart_type === 'panel_line_chart') {
            var panel_x_axis_column = $('#panel-line__x-axis_column').val();
            var data = buildDataWithPreset(preset, chart_data, ['value', panel_x_axis_column]);
            chartObject = panelLinechartObject(data,
                panel_x_axis_column,
                'Ethnicity',
                $('#chart_title').val(),
                '',
                '',
                getNumberFormat(),
                'Ethnicity-order');
        }
        return chartObject;
    }

    function buildDataWithPreset(preset, data, columns) {
        var rows = [['Ethnicity', 'Ethnicity-parent', 'Ethnicity-order'].concat(columns)];

        var body = _.clone(data);
        var headers = body.shift();
        var lowHeaders = _.map(headers, function (header) {
            return header.toLowerCase().trim()
        });
        var indices = _.map(columns, function (col) {
            var lowCol = col.toLowerCase().trim();
            return lowHeaders.indexOf(lowCol);
        });

        for (var r in preset['data']) {
            var item = preset['data'][r];
            var row = [item['preset'], item['parent'], item['order']];
            row = row.concat(_.map(indices, function (index) {
                return index === -1 ? '' : body[r][index]
            }));
            rows = rows.concat([row])
        }

        return rows;
    }

    function getPresetWithCode(code) {
        for (p in presets) {
            if (presets[p].preset.code === code) {
                return presets[p];
            }
        }
        return null;
    }


    /*
    EVENT HANDLERS
    */

    // Switch CHART_OPTIONS panels
    $('#ethnicity_settings').change(preview);

    // Switch CHART_OPTIONS panels
    $('#chart_type_selector').change(function () {
        selectChartType($(this).val())
        preview()
    });

    function selectChartType(chart_type) {
        $('#chart_type_selector').val(chart_type);
        $('.chart-option-group').hide();
        if (chart_type !== 'none') {
            $('#' + chart_type + "_options").show();
            $('#chart_format_options').show();
        }
        $('#preview_section').show();
    }

    function selectPreset(preset) {
        $('#ethnicity_settings').val(preset);
    }

    /*
    CHART PANEL events
    */

    // LINE events
    $('#line__x-axis_column').change(preview);

    // GROUPED-BAR events
    $('#grouped-bar__data_style').change(function () {
        if ($(this).val() === "ethnicity_as_group") {
            $('#grouped-bar__ethnicity_is_group').show();
            $('#grouped-bar__ethnicity_is_bar').hide();
        } else {
            $('#grouped-bar__ethnicity_is_group').hide();
            $('#grouped-bar__ethnicity_is_bar').show();
        }
        preview();
    });
    $('#grouped-bar__bar_column').change(preview);
    $('#grouped-bar__bar_order').change(preview);
    $('#grouped-bar__groups_column').change(preview);
    $('#grouped-bar__groups_order').change(preview);


    // COMPONENT events
    $('#component__data_style').change(function () {
        if ($(this).val() === "ethnicity_as_bar") {
            $('#component__ethnicity_is_bar').show();
            $('#component__ethnicity_is_sections').hide();
        } else {
            $('#component__ethnicity_is_bar').hide();
            $('#component__ethnicity_is_sections').show();
        }
        preview();
    });
    $('#component__section_column').change(preview);
    $('#component__section_order').change(preview);
    $('#component__bar_column').change(preview);
    $('#component__bar_order').change(preview);

    // PANEL-BAR events
    $('#panel-bar__data_style').change(function () {
        if ($(this).val() === "ethnicity_as_panel_bars") {
            $('#panel-bar__ethnicity_as_bar').show();
            $('#panel-bar__ethnicity_as_panels').hide();
        } else {
            $('#panel-bar__ethnicity_as_bar').hide();
            $('#panel-bar__ethnicity_as_panels').show();
        }
        preview();
    });
    $('#panel-bar__bar_column').change(preview);
    $('#panel-bar__bar_order').change(preview);
    $('#panel-bar__panel_column').change(preview);
    $('#panel-bar__panel_order').change(preview);

    // PANEL-LINE events
    $('#panel-line__x-axis_column').change(preview);


    // Show-hide NUMBER-FORMAT__OTHER panel
    $('#number_format').change(function () {
        if ($(this).val() === 'other') {
            $('#other_number_format').show()
        } else {
            $('#other_number_format').hide()
        }
        preview();
    });


    function initialiseForm() {
        if (settings.data) {
            var data_text = _.map(settings.data, function (d) {
                return d.join('\t')
            }).join('\n');
            $('#data_text_area').val(data_text);

            handleNewData(function () {
                $('#data-panel').hide();
                $('#edit-panel').show();
                setupChartbuilderWithSettings(settings);
                preview()
            })
        }
    }

    function setupChartbuilderWithSettings(settings) {
        $('#chart_type_selector').val(settings.type);
        selectChartType(settings.type);
        if (settings.preset) {
            selectPreset(settings.preset);
        }

        $('#chart_title').val(settings.chartFormat.chart_title);

        switch (settings.type) {
            case 'line_graph':
                var columnValue = settings.chartOptions.x_axis_column;
                $('#line__x-axis_column').val(columnValue);
                break;
            case 'grouped_bar_chart':
                var dataStyle = settings.chartOptions.data_style;
                $('#grouped-bar__data_style').val(dataStyle);
                if (dataStyle === 'ethnicity_as_group') {
                    $('#grouped-bar__bar_column').val(settings.chartOptions.bar_column);
                    $('#grouped-bar__ethnicity_is_group').show();
                    $('#grouped-bar__ethnicity_is_bar').hide();
                } else {
                    $('#grouped-bar__groups_column').val(settings.chartOptions.group_column);
                    $('#grouped-bar__ethnicity_is_group').hide();
                    $('#grouped-bar__ethnicity_is_bar').show();
                }
                break;
            case 'component_chart':
                var dataStyle = settings.chartOptions.data_style;
                $('#component__data_style').val(dataStyle);
                if (dataStyle === 'ethnicity_as_sections') {
                    $('#component__bar_column').val(settings.chartOptions.bar_column);
                    $('#component__bar_order').val(settings.chartOptions.bar_order);
                    $('#component__ethnicity_is_sections').show();
                    $('#component__ethnicity_is_bar').hide();
                } else {
                    $('#component__section_column').val(settings.chartOptions.section_column);
                    $('#component__section_order').val(settings.chartOptions.section_order);
                    $('#component__ethnicity_is_sections').hide();
                    $('#component__ethnicity_is_bar').show();
                }
                break;
            case 'panel_bar_chart':
                var dataStyle = settings.chartOptions.data_style;
                $('#panel-bar__data_style').val(dataStyle);
                if (dataStyle === 'ethnicity_as_panels') {
                    $('#panel-bar__bar_column').val(settings.chartOptions.bar_column);
                    $('#panel-bar__bar_order').val(settings.chartOptions.bar_order);
                    $('#panel-bar__ethnicity_as_bar').hide();
                    $('#panel-bar__ethnicity_as_panels').show();
                } else {
                    $('#panel-bar__panel_column').val(settings.chartOptions.panel_column);
                    $('#panel-bar__panel_order').val(settings.chartOptions.panel_order);
                    $('#panel-bar__ethnicity_as_bar').show();
                    $('#panel-bar__ethnicity_as_panels').hide();
                }
                break;
            case 'panel_line_chart':
                var columnValue = settings.chartOptions.x_axis_column;
                $('#panel-line__x-axis_column').val(columnValue);
                break;
            default:
                break;
        }
        $('#number_format').val(settings.chartFormat.number_format);
        $('#number_format_prefix').val(settings.chartFormat.number_format_prefix);
        $('#number_format_suffix').val(settings.chartFormat.number_format_suffix);
        $('#number_format_min').val(settings.chartFormat.number_format_min);
        $('#number_format_max').val(settings.chartFormat.number_format_max);
        if (settings.chartFormat.number_format === 'other') {
            $('#other_number_format').show();
        }
    }

    initialiseForm();
});

/*
Custom number format is far more complicated than it needs to be
However it is viable to just use this function to grab it until it becomes a problem
*/

function getNumberFormat() {
    var format = $('#number_format').val();
    if (format === 'none') {
        return { 'multiplier': 1.0, 'prefix': '', 'suffix': '', 'min': '', 'max': '' }
    } else if (format === 'percent') {
        return { 'multiplier': 1.0, 'prefix': '', 'suffix': '%', 'min': 0.0, 'max': 100.0 }
    } else if (format === 'other') {
        return {
            'multiplier': 1.0,
            'prefix': $('#number_format_prefix').val(),
            'suffix': $('#number_format_suffix').val(),
            'min': $('#number_format_min').val(),
            'max': $('#number_format_max').val()
        }
    }
}

function getTips() {

    // 1. Basics
    var basicErrors = validateChart(chart_data);
    if (basicErrors.length !== 0) {
        return basicErrors;
    }

    // 2. Required fields
    var missingFields = checkRequiredFields();
    if (missingFields.length !== 0) {
        return missingFields
    }

    // 3. Data errors
    var ethnicityColumn = getEthnicityColumn();
    var secondaryColumn = getSecondaryColumn();

    var dataErrors = validateData(chart_data, ethnicityColumn, secondaryColumn);
    return dataErrors;
}

var MISSING_FIELD_ERROR = 'Missing field error';

function checkRequiredFields() {
    var chartType = $('#chart_type_selector').val();
    switch (chartType) {
        case 'bar_chart':
            return [];
            ;
            break;
        case 'line_graph':
            if ($('#line__x-axis_column').val() === '[Required]') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'line__x-axis_column' }]
            }
            ;
            break;
        case 'grouped_bar_chart':
            if ($('#grouped-bar__data_style').val() === 'ethnicity_as_group') {
                if ($('#grouped-bar__bar_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'grouped-bar__bar_column' }]
                }
                ;
            } else {
                if ($('#grouped-bar__groups_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'grouped-bar__groups_column' }]
                }
                ;
            }
            break;
        case 'component_chart':
            if ($('#component__data_style').val() === 'ethnicity_as_sections') {
                if ($('#component__bar_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'component__bar_column' }]
                }
                ;
            } else {
                if ($('#component__section_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'component__section_column' }]
                }
                ;
            }
            break;
        case 'panel_bar_chart':
            if ($('#panel-bar__data_style').val() === 'ethnicity_as_panels') {
                if ($('#panel-bar__bar_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-bar__bar_column' }]
                }
                ;
            } else {
                if ($('#panel-bar__panel_column').val() === '[Required]') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-bar__panel_column' }]
                }
                ;
            }
            break;
        case 'panel_line_chart':
            if ($('#panel-line__x-axis_column').val() === '[Required]') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-line__x-axis_column' }]
            }
            ;
            break;
        default:
            return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'chart_type_selector' }]
    }
    return [];
}


function getEthnicityColumn() {
    for (var i in chart_data[0]) {
        var lower = chart_data[0][i].toLowerCase();
        if (lower.search('ethnic') >= 0) {
            return chart_data[0][i]
        }
    }
    return null
}

function getSecondaryColumn() {
    var chartType = $('#chart_type_selector').val();
    switch (chartType) {
        case 'bar_chart':
            return null;
        case 'line_graph':
            return $('#line__x-axis_column').val();
        case 'grouped_bar_chart':
            if ($('#grouped-bar__data_style').val() === 'ethnicity_as_group') {
                return $('#grouped-bar__bar_column').val()
            } else {
                return $('#grouped-bar__groups_column').val()
            }
        case 'component_chart':
            if ($('#component__data_style').val() === 'ethnicity_as_sections') {
                return $('#component__bar_column').val()
            } else {
                return $('#component__section_column').val()
            }
        case 'panel_bar_chart':
            if ($('#panel-bar__data_style').val() === 'ethnicity_as_panels') {
                return $('#panel-bar__bar_column').val()
            } else {
                return $('#panel-bar__panel_column').val()
            }
        case 'panel_line_chart':
            return $('#panel-line__x-axis_column').val();
        default:
            return null;
    }
}

function pasteJson(json) {
    var data_text_area = document.getElementById('data_text_area');

    data_text_area.value = _.map(json, function (row) {
        return row.join('\t');
    }).join('\n');
    data_text_area.dispatchEvent(new Event("keyup"));
}