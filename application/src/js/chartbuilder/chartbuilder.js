
/*
    Functionality of chartbuilder including the main methods that run each stage


    On open **initialiseForm()**
    - grab current_settings from dimension.chart_settings_and_source_data if such a thing exists
    - if current_settings doesn't exist open with the data area open.
    - otherwise set the current_settings from file, paste data into the data panel and run the On new data routine below

    On new data (changing data in the data panel area and clicking OK) **handleNewData()**
    - use an AJAX call to the /get-valid-classifications-for-data endpoint to add extra values **buildDataWithClassifications()**
    - populate the chart builder dropdowns with correct values **populateChartOptions(), populateEthnicityClassifications()**
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
var classifications = [];
var chart_data = null;

// Variables that needs to be maintained when the user makes changes to the text data
var current_data = "";
var current_settings = null;

$(document).ready(function () {

    // add events to buttons
    document.getElementById('confirm-data').addEventListener('click', setChartData)
    document.getElementById('edit-data').addEventListener('click', editChartData)
    document.getElementById('cancel-edit-data').addEventListener('click', cancelEditData)
    document.getElementById('save').addEventListener('click', saveChart)

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
        document.getElementById('data-panel').classList.add('hidden')
        document.getElementById('edit-panel').classList.remove('hidden')
        document.getElementById('builder-title').textContent = 'Format and view chart'
    }

    function editChartData(evt) {
        current_data = $('#data_text_area').val();
        current_settings = getChartPageSettings();
        document.getElementById('data-panel').classList.remove('hidden')
        document.getElementById('edit-panel').classList.add('hidden')
        document.getElementById('builder-title').textContent = 'Create a chart'
    }

    function cancelEditData(evt) {
        $('#data_text_area').val(current_data);
        document.getElementById('data-panel').classList.add('hidden')
        document.getElementById('edit-panel').classList.remove('hidden')
        document.getElementById('builder-title').textContent = 'Format and view chart'
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

        document.getElementById('data-description').innerHTML = message;

        // update options in drop-downs
        var headers = chart_data[0];
        populateChartOptions(headers);

        // call the backend to do the presets heavy lifting
        var ethnicity_data = getEthnicityValues(chart_data);
        $.ajax({
            type: "post",
            url: url_get_classifications,
            dataType: 'json',
            data: JSON.stringify({ 'data': ethnicity_data }),
            contentType: 'application/json; charset=utf-8',
            success: function (response) {
                // upon heavy lifting complete

                // populate the ethnicity presets from the response
                classifications = response['classifications'];
                populateEthnicityClassifications(classifications);
                showHideCustomEthnicityPanel();

                // show the presets (step 2) and chart type (step 3) section
                document.getElementById('ethnicity_settings_section').classList.remove('hidden')
                document.getElementById('select_chart_type').classList.remove('hidden')


                // any further processing
                if (on_success) {
                    on_success();
                }
            },
            failure: function () {
                console.log('failed to get ethnicity classifcations');
            },
            error: function (err) {
                console.log(err);
            }
        });
    }

    function getEthnicityValues(data) {
        var all_data = _.clone(data);
        var headers = all_data.shift();

        var column = getEthnicityColumn(headers);
        if (column >= 0) {
            return _.pluck(all_data, column);
        }
        return [];
    }

    function getEthnicityColumn(headers) {
        for (var index = 0; index < headers.length; index++) {
            var cleanHeader = headers[index].toLowerCase().trim();
            if (cleanHeader.indexOf('ethnic') >= 0) {
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
        var listWithRequired = dropdownHtmlWithDefault(headers, 'Please select');

        document.getElementById('line__x-axis_column').innerHTML = listWithRequired

        document.getElementById('grouped-bar__bar_column').innerHTML = listWithRequired
        document.getElementById('grouped-bar__groups_column').innerHTML = listWithRequired

        document.getElementById('component__bar_column').innerHTML = listWithRequired
        document.getElementById('component__bar_order').innerHTML = listWithNone
        document.getElementById('component__section_column').innerHTML = listWithRequired
        document.getElementById('component__section_order').innerHTML = listWithNone

        document.getElementById('panel-bar__panel_column').innerHTML = listWithRequired
        document.getElementById('panel-bar__panel_order').innerHTML = listWithNone
        document.getElementById('panel-bar__bar_column').innerHTML = listWithRequired
        document.getElementById('panel-bar__bar_order').innerHTML = listWithNone

        document.getElementById('panel-line__x-axis_column').innerHTML = listWithRequired
    }

    function selectDropdown(dropdown_id, value) {
        var dropdown = document.getElementById(dropdown_id);
        for (var i = 0; i < dropdown.length; i++) {
            dropdown[i].selected = (dropdown[i].value === value)
        }
    }


    function showHideCustomEthnicityPanel() {
        if($('#ethnicity_settings').val() === 'custom') {
            document.getElementById('custom_classification__panel').classList.remove('hidden')
        } else {
            document.getElementById('custom_classification__panel').classList.add('hidden')
        }
    }

    function populateEthnicityClassifications(classifications) {
        var html = '';
        for (var c in classifications) {
            var classification_name = classifications[c]['classification']['name'];
            var classification_id = classifications[c]['classification']['id'];
            if (c === 0) {
                html = html + '<option value="' + classification_id + '" selected>' + classification_name + '</option>';
            } else {
                html = html + '<option value="' + classification_id + '" >' + classification_name + '</option>';
            }
        }
        document.getElementById('ethnicity_settings').innerHTML = html
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
        document.getElementById('tips_container').classList.remove('hidden')
        document.getElementById('preview_container').classList.add('hidden')

        document.getElementById('notes_container').classList.add('hidden')
        document.getElementById('errors_container').classList.add('hidden')

        var tip_list = document.getElementById('tip-list')
        for (var i = 0; i < tip_list.children.length; i++) {
            tip_list.children[i].classList.add('hidden')
        }

        if (tipsOfType(tips, MISSING_FIELD_ERROR).length > 0) {
            document.getElementById('notes_container').classList.remove('hidden')
        }
        if (tipsOfType(tips, ETHNICITY_ERROR).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__ethnicity-column').classList.remove('hidden')
        }
        if (tipsOfType(tips, VALUE_ERROR).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__value-column').classList.remove('hidden')
        }
        if (tipsOfType(tips, RECTANGLE_ERROR).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__rectangular-data').classList.remove('hidden')
        }
        if (tipsOfType(tips, DATA_ERROR_COMPLEX_DATA).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__complex-data').classList.remove('hidden')
        }
        if (tipsOfType(tips, DATA_ERROR_DUPLICATION).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__duplicate-data').classList.remove('hidden')
        }
        if (tipsOfType(tips, DATA_ERROR_MISSING_DATA).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__missing-data').classList.remove('hidden')
        }

    }

    function tipsOfType(tips, errorType) {
        return _.filter(tips, function (tip) {
            return tip.errorType === errorType;
        })
    }

    function displayChart() {
        document.getElementById('tips_container').classList.add('hidden')
        document.getElementById('preview_container').classList.remove('hidden')

        var chartObject = buildChartObject();
        if (chartObject) {
            chartObject.title = '';
            drawChart('container', chartObject);

            document.getElementById('save_section').classList.remove('hidden')
        }

        document.getElementById('chart_title').dispatchEvent(new Event("input"));
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
                data: JSON.stringify({
                    'chartObject': chartObject,
                    'source': src,
                    'classificationCode': getClassificationCode(),
                    'customClassificationCode': getCustomClassificationCode(),
                    'customClassification': getCustomObject(),
                    'ethnicityValues': getEthnicityValues(chart_data)}),
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
            'preset': getClassificationCode(),
            'custom': getCustomObject(),
            'chartOptions': getChartTypeOptions(chartType),
            'chartFormat': getChartFormat(),
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

    function getClassificationCode() {
        return $('#ethnicity_settings').val();
    }

    function getCustomClassificationCode() {
        return $('#custom_classification__selector').val();
    }

    function getCustomHasParents() {
        return $('#custom_classification__has_parents').prop('checked');
    }

    function getCustomHasAll() {
        return $('#custom_classification__has_all').prop('checked');
    }

    function getCustomHasUnknown() {
        return $('#custom_classification__has_unknown').prop('checked');
    }

    function getCustomObject() {
        return {
            'code': getCustomClassificationCode(),
            'hasParents': getCustomHasParents(),
            'hasAll': getCustomHasAll(),
            'hasUnknown': getCustomHasUnknown()
        }
    }

    function buildChartObject() {
        var chart_type = $('#chart_type_selector').val();
        var chartObject = null;
        var classification = getClassificationById($('#ethnicity_settings').val());
        if (chart_type === 'bar_chart') {
            chartObject = barchartObject(buildDataWithClassifications(classification, chart_data, ['value']),
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
            chartObject = linechartObject(buildDataWithClassifications(classification, chart_data, ['value', x_axis_column]),
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
                chartObject = barchartObject(buildDataWithClassifications(classification, chart_data, ['value', barColumn]),
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
                chartObject = barchartObject(buildDataWithClassifications(classification, chart_data, ['value', groupColumn]),
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
                    data = buildDataWithClassifications(classification, chart_data, ['value', sectionColumn, sectionOrder])
                } else {
                    data = buildDataWithClassifications(classification, chart_data, ['value', sectionColumn])
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
                    data = buildDataWithClassifications(classification, chart_data, ['value', groupColumn, groupOrder])
                } else {
                    data = buildDataWithClassifications(classification, chart_data, ['value', groupColumn])
                }
                chartObject = componentChartObject(buildDataWithClassifications(classification, chart_data, ['value', groupColumn]),
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
                    data = buildDataWithClassifications(classification, chart_data, ['value', panelColumn, panelOrder])
                } else {
                    data = buildDataWithClassifications(classification, chart_data, ['value', panelColumn])
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
                    data = buildDataWithClassifications(classification, chart_data, ['value', panelBarColumn, panelBarOrder])
                } else {
                    data = buildDataWithClassifications(classification, chart_data, ['value', panelBarColumn])
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
            var data = buildDataWithClassifications(classification, chart_data, ['value', panel_x_axis_column]);
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

    function buildDataWithClassifications(classification, data, columns) {
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

        for (var r in classification['data']) {
            var item = classification['data'][r];
            var row = [item['display_value'], item['parent'], item['order']];
            row = row.concat(_.map(indices, function (index) {
                return index === -1 ? '' : body[r][index]
            }));
            rows = rows.concat([row])
        }

        return rows;
    }

    function getClassificationById(classification_id) {
        for (c in classifications) {
            if (classifications[c].classification.id === classification_id) {
                return classifications[c];
            }
        }
        return null;
    }


    /*
    EVENT HANDLERS
    */

    // Switch CHART_OPTIONS panels
    $('#ethnicity_settings').change(function () {
        showHideCustomEthnicityPanel();
        preview();
    })
    $('#custom_classification__selector').change(preview);

    // Switch CHART_OPTIONS panels
    $('#chart_type_selector').change(function () {
        selectChartType($(this).val())
        preview()
    });

    function selectChartType(chart_type) {
        $('#chart_type_selector').val(chart_type);

        var chartOptionGroupDivs = document.getElementsByClassName('chart-option-group')

        for (var i = 0; i < chartOptionGroupDivs.length; i++) {
            chartOptionGroupDivs[i].classList.add('hidden')
        }

        if (chart_type !== 'none') {
            document.getElementById(chart_type + '_options').classList.remove('hidden')
            document.getElementById('chart_format_options').classList.remove('hidden')
        }
    }

    function selectClassification(classification) {
        $('#ethnicity_settings').val(classification);
    }

    function selectCustomValues(customObject) {
        selectCustomClassification(customObject['code'])
        selectCustomHasParents(customObject['hasParents'])
        selectCustomHasAll(customObject['hasAll'])
        selectCustomHasUnknown(customObject['hasUnknown'])
    }

    function selectCustomClassification(customClassification) {
        $('#custom_classification__selector').val(customClassification)
    }

    function selectCustomHasParents(customValue) {
           $('#custom_classification__has_parents').prop('checked', customValue)
    }

    function selectCustomHasUnknown(customValue) {
            $('#custom_classification__has_unknown').prop('checked', customValue)
    }

    function selectCustomHasAll(customValue) {
            $('#custom_classification__has_all').prop('checked', customValue)
    }

    /*
    CHART PANEL events
    */

    // LINE events
    $('#line__x-axis_column').change(preview);

    // GROUPED-BAR events
    $('#grouped-bar__data_style').change(function () {
        if ($(this).val() === "ethnicity_as_group") {
            document.getElementById('grouped-bar__ethnicity_is_group').classList.remove('hidden')
            document.getElementById('grouped-bar__ethnicity_is_bar').classList.add('hidden')
        } else {
            document.getElementById('grouped-bar__ethnicity_is_group').classList.add('hidden')
            document.getElementById('grouped-bar__ethnicity_is_bar').classList.remove('hidden')
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
            document.getElementById('component__ethnicity_is_bar').classList.remove('hidden')
            document.getElementById('component__ethnicity_is_sections').classList.add('hidden')
        } else {
            document.getElementById('component__ethnicity_is_bar').classList.add('hidden')
            document.getElementById('component__ethnicity_is_sections').classList.remove('hidden')
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
            document.getElementById('panel-bar__ethnicity_as_bar').classList.remove('hidden')
            document.getElementById('panel-bar__ethnicity_as_panels').classList.add('hidden')
        } else {
            document.getElementById('panel-bar__ethnicity_as_bar').classList.add('hidden')
            document.getElementById('panel-bar__ethnicity_as_panels').classList.remove('hidden')
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
            document.getElementById('other_number_format').classList.remove('hidden')
        } else {
            document.getElementById('other_number_format').classList.add('hidden')
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
                document.getElementById('data-panel').classList.add('hidden')
                document.getElementById('edit-panel').classList.remove('hidden')
                setupChartbuilderWithSettings(settings);
                preview()
            })
        }
    }

    function setupChartbuilderWithSettings(settings) {
        $('#chart_type_selector').val(settings.type);
        selectChartType(settings.type);
        if (settings.preset) {
            selectClassification(settings.preset);
        }
        if (settings.custom) {
            selectCustomValues(settings.custom)
        }

        showHideCustomEthnicityPanel()

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
                    document.getElementById('grouped-bar__ethnicity_is_group').classList.remove('hidden')
                    document.getElementById('grouped-bar__ethnicity_is_bar').classList.add('hidden')
                } else {
                    $('#grouped-bar__groups_column').val(settings.chartOptions.group_column);
                    document.getElementById('grouped-bar__ethnicity_is_group').classList.add('hidden')
                    document.getElementById('grouped-bar__ethnicity_is_bar').classList.remove('hidden')
                }
                break;
            case 'component_chart':
                var dataStyle = settings.chartOptions.data_style;
                $('#component__data_style').val(dataStyle);
                if (dataStyle === 'ethnicity_as_sections') {
                    $('#component__bar_column').val(settings.chartOptions.bar_column);
                    $('#component__bar_order').val(settings.chartOptions.bar_order);
                    document.getElementById('component__ethnicity_is_sections').classList.remove('hidden')
                    document.getElementById('component__ethnicity_is_bar').classList.add('hidden')
                } else {
                    $('#component__section_column').val(settings.chartOptions.section_column);
                    $('#component__section_order').val(settings.chartOptions.section_order);
                    document.getElementById('component__ethnicity_is_sections').classList.add('hidden')
                    document.getElementById('component__ethnicity_is_bar').classList.remove('hidden')
                }
                break;
            case 'panel_bar_chart':
                var dataStyle = settings.chartOptions.data_style;
                $('#panel-bar__data_style').val(dataStyle);
                if (dataStyle === 'ethnicity_as_panels') {
                    $('#panel-bar__bar_column').val(settings.chartOptions.bar_column);
                    $('#panel-bar__bar_order').val(settings.chartOptions.bar_order);
                    document.getElementById('panel-bar__ethnicity_as_bar').classList.add('hidden')
                    document.getElementById('panel-bar__ethnicity_as_panels').classList.remove('hidden')
                } else {
                    $('#panel-bar__panel_column').val(settings.chartOptions.panel_column);
                    $('#panel-bar__panel_order').val(settings.chartOptions.panel_order);
                    document.getElementById('panel-bar__ethnicity_as_bar').classList.remove('hidden')
                    document.getElementById('panel-bar__ethnicity_as_panels').classList.add('hidden')
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
            document.getElementById('other_number_format').classList.remove('hidden')
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
    var ethnicityColumn = getEthnicityColumnHeader();
    var secondaryColumn = getSecondaryColumnHeader();

    var dataErrors = validateData(chart_data, ethnicityColumn, secondaryColumn);
    return dataErrors;
}

var MISSING_FIELD_ERROR = 'Missing field error';

function checkRequiredFields() {
    if ($('#ethnicity_settings').val() === 'custom' && $('#custom_classification__selector').val() === 'Please select') {
        return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'custom_classification__selector' }]
    }

    var chartType = $('#chart_type_selector').val();

    switch (chartType) {
        case 'bar_chart':
            return [];
            ;
            break;
        case 'line_graph':
            if ($('#line__x-axis_column').val() === 'Please select') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'line__x-axis_column' }]
            }
            ;
            break;
        case 'grouped_bar_chart':
            if ($('#grouped-bar__data_style').val() === 'ethnicity_as_group') {
                if ($('#grouped-bar__bar_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'grouped-bar__bar_column' }]
                }
                ;
            } else {
                if ($('#grouped-bar__groups_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'grouped-bar__groups_column' }]
                }
                ;
            }
            break;
        case 'component_chart':
            if ($('#component__data_style').val() === 'ethnicity_as_sections') {
                if ($('#component__bar_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'component__bar_column' }]
                }
                ;
            } else {
                if ($('#component__section_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'component__section_column' }]
                }
                ;
            }
            break;
        case 'panel_bar_chart':
            if ($('#panel-bar__data_style').val() === 'ethnicity_as_panels') {
                if ($('#panel-bar__bar_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-bar__bar_column' }]
                }
                ;
            } else {
                if ($('#panel-bar__panel_column').val() === 'Please select') {
                    return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-bar__panel_column' }]
                }
                ;
            }
            break;
        case 'panel_line_chart':
            if ($('#panel-line__x-axis_column').val() === 'Please select') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'panel-line__x-axis_column' }]
            }
            ;
            break;
        default:
            return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'chart_type_selector' }]
    }
    return [];
}


function getEthnicityColumnHeader() {
    for (var i in chart_data[0]) {
        var lower = chart_data[0][i].toLowerCase();
        if (lower.search('ethnic') >= 0) {
            return chart_data[0][i]
        }
    }
    return null
}

function getSecondaryColumnHeader() {
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
