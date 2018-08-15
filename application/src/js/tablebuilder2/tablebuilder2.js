/*
    Functionality of tablebuilder including the main methods that run each stage


    On open **initialiseForm()**
    - grab current_settings from dimension.table_2_source_data if such a thing exists
    - if current_settings doesn't exist open with the data area open.
    - otherwise set the current_settings from file, paste data into the data panel and run the On new data routine below

    On new data (changing data in the data panel area and clicking Okay) **handleNewData()**
    - use an AJAX call to the /get-valid-presets-for-data endpoint to add extra values **buildDataWithPreset()**
    - populate the table builder dropdowns with correct values **populateTableOptions(), populateEthnicityPresets()**
    - if any settings currently exist apply as many as are still relevant **setupTablebuilderWithSettings()**

    On settings changes
    - validate they will make a viable table **getTips()**
    - if so use the rd table object factory and renderer to display a preview **preview()**
    - otherwise display an error and tip to fix it **displayTips()**

    On save
    - build a table object with the rd-table-object factory **buildTableObject()**
    - create a table_settings lump of json **getTablePageSettings()**
    - post both to <dimension>/create-table endpoint **postTableObject()**

 */

// The main working data variables
var presets = [];
var table_data = null;

// Variables that needs to be maintained when the user makes changes to the text data
var current_data = "";
var current_settings = null;

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

function get_ethnicity_values(data) {
    var all_data = _.clone(data);
    var headers = all_data.shift();

    var column = get_ethnicity_column(headers);
    if (column >= 0) {
        return _.pluck(all_data, column);
    }
    return [];
}

function get_is_simple_data(data) {
    var values = get_ethnicity_values(data);
    values = _.uniq(values);
    return values.length === data.length - 1
}

$(document).ready(function () {

    // add events to buttons
    $('#preview').click(preview);
    $('#confirm-data').click(setTableData);
    $('#edit-data').click(editTableData);
    $('#cancel-edit-data').click(cancelEditData);
    $('#save').click(saveTable);
    $('#exit').click(back);

    function back(evt) {
        window.location.replace(url_edit_dimension);
    }

    /*
        Events from the DATA ENTRY PANEL
     */

    function setTableData(evt) {
        handleNewData(function () {
            if (current_settings) {
                setupTablebuilderWithSettings(current_settings)
            }
            preview()
        });
        $('#data-panel').hide();
        $('#edit-panel').show();
    }

    function editTableData(evt) {
        current_data = $('#data_text_area').val();
        current_settings = getTablePageSettings();
        $('#data-panel').show();
        $('#data_text_area').focus();
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
        table_data = textToData(tabbedData);
        if (table_data.length > 0) {
            message = table_data.length - 1 + ' rows by ' + table_data[0].length + ' columns'
        }
        $('#data-description').html(message);

        // update options in drop-downs
        var headers = table_data[0];
        populateTableOptions(headers);

        // call the backend to do the presets heavy lifting
        var ethnicity_data = get_ethnicity_values(table_data);
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

                // show the presets (step 2) and table type (step 3) section
                $('#ethnicity_settings_section').show();

                if (get_is_simple_data(table_data)) {
                    $('#simple_table_options').show();
                    $('#complex_table_options').hide();
                } else {
                    $('#simple_table_options').hide();
                    $('#complex_table_options').show();
                }

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


    /*
        SETUP
    */

    function populateTableOptions(headers) {
        var listWithNone = dropdownHtmlWithDefault(headers, '[None]');
        var listWithRequired = dropdownHtmlWithDefault(headers, '[Required]');

        $('#ethnicity-as-row__columns').html(listWithRequired);
        $('#ethnicity-as-row__column_order').html(listWithNone);
        $('#ethnicity-as-column__rows').html(listWithRequired);
        $('#ethnicity-as-column__row-order').html(listWithNone);

        $('#table_column_1').html(listWithRequired);
        $('#table_column_2').html(listWithNone);
        $('#table_column_3').html(listWithNone);
        $('#table_column_4').html(listWithNone);
        $('#table_column_5').html(listWithNone);
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
        var exclude = [];
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
        Render the table as a preview using drawTable() from rd-graph.js
        (this the exact same method that is used front-end)
    */

    function dataColumnChange(evt, columnName) {
        if ($('#' + this.id + '_name').val() === "") {
            $('#' + this.id + '_name').val($('#' + this.id + ' option:selected').val());
        };

        preview(evt);
    }

    function preview(evt) {
        var tips = getTips();
        if (tips.length > 0) {
            displayTips(tips);
        } else {
            displayTable();
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
        if (tipsOfType(tips, RECTANGLE_ERROR).length > 0) {
            $("#errors_container").show();
            $('#tip__rectangular-data').show();
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

    function displayTable() {
        $('#tips_container').hide();
        $('#preview_container').show();

        var tableObject = innerBuildTableObject();
        if (tableObject) {
            if (tableObject.title && tableObject.title.text) {
                $('#title-container').html('<h3 class="heading-small">' + tableObject.title.text + '</h3>');
            }
            tableObject.title = '';
            drawTable('container', tableObject);

            $('#save_section').show();
        }
    }

    /*
        SAVE
        Save the table by building a tableObject and bundling up all the setting then sending it to the backend
    */

    function saveTable(evt) {

        $('#save').attr('disabled', 'disabled');

        var tableObject = innerBuildTableObject();
        var tableBuilderSettings = getTablePageSettings();
        if (tableObject) {
            postTableObject(tableObject, tableBuilderSettings);
        }
    }

    function postTableObject(tableObject, src) {
        if (tableObject) {
            // adjust for null data
            $.each(tableObject.series, function () {
                for (var i = 0; i < this.data.length; i++) {
                    if (isNaN(this.data[i].y)) {
                        this.data[i].y = 0;
                    }
                }
            });

            $.ajax({
                type: "POST",
                url: url_save_table_to_page,
                dataType: 'json',
                data: JSON.stringify({ 'tableObject': tableObject, 'source': src, 'tableBuilderVersion': 2 }),
                contentType: 'application/json',
                success: function () {
                    location.reload();
                }
            });
        }
    }

    function getTablePageSettings() {
        // get the data
        var tabbedData = $("#data_text_area").val();
        return {
            'data': textToData(tabbedData),
            'preset': getPresetCode(),
            'tableOptions': getTableTypeOptions(),
            'tableValues': getTableValues(),
            'version': '2.0'
        }
    }

    function getTableTypeOptions() {
        if (get_is_simple_data(table_data)) {
            return {};
        }
        else {
            var dataStyle = $('#complex-table__data-style').val();

            var selection = dataStyle === 'ethnicity_as_row' ? $('#ethnicity-as-row__columns').val() : $('#ethnicity-as-column__rows').val();
            var order = dataStyle === 'ethnicity_as_row' ? $('#ethnicity-as-row__column-order').val() : $('#ethnicity-as-column__row-order').val();

            return {
                'data_style': $('#complex-table__data-style').val(),
                'selection': selection,
                'order': order,
            }
        }
    }

    function getTableValues() {
        return {
            'table_title': $('#table_title').val(),
            'table_column_1': $('#table_column_1').val(),
            'table_column_1_name': $('#table_column_1_name').val(),
            'table_column_2': $('#table_column_2').val(),
            'table_column_2_name': $('#table_column_2_name').val(),
            'table_column_3': $('#table_column_3').val(),
            'table_column_3_name': $('#table_column_3_name').val(),
            'table_column_4': $('#table_column_4').val(),
            'table_column_4_name': $('#table_column_4_name').val(),
            'table_column_5': $('#table_column_5').val(),
            'table_column_5_name': $('#table_column_5_name').val(),
        }
    }

    function getPresetCode() {
        return $('#ethnicity_settings').val();
    }

    function buildTableColumns() {
        var columns = []
        $('.column_option_picker').each(function (idx) { if ($(this).val() !== '[None]') { columns.push($(this).val()); }; });
        return columns
    }

    function buildEthnicityByRowColumns() {
        var columns = [$('#ethnicity-as-row__columns').val()]
        if ($('#ethnicity-as-row__column-order').val() !== '[None]') {
            columns.push($('#ethnicity-as-row__column-order').val())
        }
        return columns
    }

    function buildEthnicityByColumnColumns() {
        var columns = [$('#ethnicity-as-column__rows').val()]
        if ($('#ethnicity-as-column__row-order').val() !== '[None]') {
            columns.push($('#ethnicity-as-column__row-order').val())
        }
        return columns
    }

    function buildTableColumnNames() {
        var columns = []
        $('.column_option_picker_name').each(function (idx) { if ($(this).val() !== '') { columns.push($(this).val()); }; });
        return columns
    }


    function innerBuildTableObject() {
        var tableObject = null;
        var preset = getPresetWithCode($('#ethnicity_settings').val());
        if (get_is_simple_data(table_data)) {
            tableObject = buildTableObject(buildDataWithPreset(preset, table_data, buildTableColumns()),
                $('#table_title').val(),
                '',
                '',
                'Ethnicity',
                'Ethnicity-parent',
                '[None]',
                'Ethnicity-order',
                buildTableColumns(),
                buildTableColumnNames(),
                'Ethnicity',
                '[None]');
        } else {
            if ($('#complex-table__data-style').val() === 'ethnicity_as_row') {
                var all_table_columns = buildTableColumns().concat(buildEthnicityByRowColumns());
                tableObject = buildTableObject(buildDataWithPreset(preset, table_data, all_table_columns),
                    $('#table_title').val(),
                    '',
                    '',
                    'Ethnicity',
                    'Ethnicity-parent',
                    $('#ethnicity-as-row__columns').val(),
                    'Ethnicity-order',
                    buildTableColumns(),
                    buildTableColumnNames(),
                    'Ethnicity',
                    $('#ethnicity-as-row__column_order').val());
            } else {
                var all_table_columns = buildTableColumns().concat(buildEthnicityByColumnColumns());
                tableObject = buildTableObject(buildDataWithPreset(preset, table_data, all_table_columns),
                    $('#table_title').val(),
                    '',
                    '',
                    $('#ethnicity-as-column__rows').val(),
                    '',
                    'Ethnicity',
                    $('#ethnicity-as-column__row_order').val(),
                    buildTableColumns(),
                    buildTableColumnNames(),
                    '',
                    'Ethnicity-order');
            }
        }
        return tableObject;
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
    // Switch TABLE_OPTIONS panels
    $('#ethnicity_settings').change(preview);

    function selectPreset(preset) {
        $('#ethnicity_settings').val(preset);
    }

    /*
        TABLE PANEL events
    */

    // COMPLEX TABLE events
    $('#complex-table__data-style').change(function () {
        selectDataStyle();
        preview();
    });
    $('#ethnicity-as-row__columns').change(preview);
    $('#grouped-bar__bar_order').change(preview);
    $('#ethnicity-as-column__rows').change(preview);
    $('#grouped-bar__groups_order').change(preview);

    $('#table_column_1_name').change(preview);
    $('#table_column_1').change(dataColumnChange);
    $('#table_column_2_name').change(preview);
    $('#table_column_2').change(dataColumnChange);
    $('#table_column_3_name').change(preview);
    $('#table_column_3').change(dataColumnChange);
    $('#table_column_4_name').change(preview);
    $('#table_column_4').change(dataColumnChange);
    $('#table_column_5_name').change(preview);
    $('#table_column_5').change(dataColumnChange);

    function selectDataStyle() {
        if ($('#complex-table__data-style').val() === "ethnicity_as_row") {
            $('#complex-table__ethnicity-is-row').show();
            $('#complex-table__ethnicity-is-column').hide();
        } else {
            $('#complex-table__ethnicity-is-row').hide();
            $('#complex-table__ethnicity-is-column').show();
        }
    }


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
                setupTablebuilderWithSettings(settings);
                preview()
            })
        }
    };

    function setupTablebuilderWithSettings(settings) {
        if (settings.preset) {
            selectPreset(settings.preset);
        }

        $('#table_title').val(settings.tableValues.table_title);
        $('#complex-table__data-style').val(settings.tableOptions.data_style);

        if (settings.tableOptions.data_style === 'ethnicity_as_row') {
            $('#ethnicity-as-row__columns').val(settings.tableOptions.selection);
            $('#ethnicity-as-row__column-order').val(settings.tableOptions.order);
        } else {
            $('#ethnicity-as-column__rows').val(settings.tableOptions.selection);
            $('#ethnicity-as-column__row-order').val(settings.tableOptions.order);
        }

        selectDataStyle();

        $('#table_column_1').val(settings.tableValues.table_column_1);
        $('#table_column_1_name').val(settings.tableValues.table_column_1_name);
        $('#table_column_2').val(settings.tableValues.table_column_2);
        $('#table_column_2_name').val(settings.tableValues.table_column_2_name);
        $('#table_column_3').val(settings.tableValues.table_column_3);
        $('#table_column_3_name').val(settings.tableValues.table_column_3_name);
        $('#table_column_4').val(settings.tableValues.table_column_4);
        $('#table_column_4_name').val(settings.tableValues.table_column_4_name);
        $('#table_column_5').val(settings.tableValues.table_column_5);
        $('#table_column_5_name').val(settings.tableValues.table_column_5_name);
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
    var basicErrors = validateTable(table_data);
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

    var dataErrors = validateData(table_data, ethnicityColumn, secondaryColumn);
    return dataErrors;
}

var MISSING_FIELD_ERROR = 'Missing field error';

function checkRequiredFields() {
    if (get_is_simple_data(table_data) === false) {
        if ($('#complex-table__data-style').val() === 'ethnicity_as_row') {
            if ($('#ethnicity-as-row__columns').val() === '[Required]') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-row__columns' }]
            };
        } else {
            if ($('#ethnicity-as-column__rows').val() === '[Required]') {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-column__rows' }]
            };
        }
    }

    if ($('#table_column_1').val() === '[Required]') {
        return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'table_column_1' }]
    }

    return [];
}

function getEthnicityColumn() {
    for (var i in table_data[0]) {
        var lower = table_data[0][i].toLowerCase();
        if (lower.search('ethnic') >= 0) {
            return table_data[0][i]
        }
    }
    return null
}

function getSecondaryColumn() {
    if (get_is_simple_data(table_data)) {
        return null;
    } else {
        if ($('#complex-table__data-style').val() === 'ethnicity_as_row') {
            return $('#ethnicity-as-row__columns').val()
        } else {
            return $('#ethnicity-as-column__rows').val()
        }
    }
}

/*
    Helper for selenium tests
*/

function pasteJson(json) {
    var data_text_area = document.getElementById('data_text_area');

    data_text_area.value = _.map(json, function (row) {
        return row.join('\t');
    }).join('\n');
    data_text_area.dispatchEvent(new Event("keyup"));
}