/*
    Functionality of tablebuilder including the main methods that run each stage


    On open **initialiseForm()**
    - grab current_settings from dimension.table_2_source_data if such a thing exists
    - if current_settings doesn't exist open with the data area open.
    - otherwise set the current_settings from file, paste data into the data panel and run the On new data routine below

    On new data (changing data in the data panel area and clicking OK) **handleNewData()**
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

var unselectedOptionString = "Please select";

function getEthnicityColumn(headers) {
    for (var index = 0; index < headers.length; index++) {
        var cleanHeader = headers[index].toLowerCase().trim();
        if (cleanHeader.indexOf('ethnic') >= 0) {
            return index
        }
    }
    return -1;
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

function getIsSimpleData(data) {
    var values = getEthnicityValues(data);
    values = _.uniq(values);
    return values.length === data.length - 1
}

document.addEventListener('DOMContentLoaded', function() {

    // add events to buttons
    document.getElementById('confirm-data').addEventListener('click', setTableData)
    document.getElementById('edit-data').addEventListener('click', editTableData)
    document.getElementById('cancel-edit-data').addEventListener('click', cancelEditData)
    document.getElementById('save').addEventListener('click', saveTable)

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

        document.getElementById('data-panel').classList.add('hidden')
        document.getElementById('edit-panel').classList.remove('hidden')
        document.getElementById('builder-title').innerHTML = 'Format and view table';
    }

    function editTableData(evt) {
        current_data = document.getElementById('data_text_area').value
        current_settings = getTablePageSettings();

        document.getElementById('data-panel').classList.remove('hidden')
        document.getElementById('data_text_area').focus()
        document.getElementById('edit-panel').classList.add('hidden')
        document.getElementById('builder-title').innerHTML = 'Create a table';
    }

    function cancelEditData(evt) {
        document.getElementById('data_text_area').value = current_data;
        document.getElementById('data-panel').classList.add('hidden')
        document.getElementById('edit-panel').classList.remove('hidden')
        document.getElementById('builder-title').innerHTML = 'Format and view table';
    }


    /*
        Initialise the main editor after DATA ENTRY PANEL change
    */

    function handleNewData(on_success) {

        // get the data
        var tabbedData = document.getElementById('data_text_area').value

        // set the DATA DISPLAY content
        table_data = textToData(tabbedData);
        if (table_data.length > 0) {
            message = table_data.length - 1 + ' rows by ' + table_data[0].length + ' columns'
        }
        document.getElementById('data-description').innerHTML = message;

        // update options in drop-downs
        var headers = table_data[0];
        populateTableOptions(headers);

        // call the backend to do the presets heavy lifting
        var ethnicity_data = getEthnicityValues(table_data);
        $.ajax({
            type: "post",
            url: url_get_classifications,
            dataType: 'json',
            data: JSON.stringify({'data': ethnicity_data}),
            contentType: 'application/json; charset=utf-8',
            success: function (response) {
                // upon heavy lifting complete

                // populate the ethnicity presets from the response
                presets = response['presets'];
                populateEthnicityPresets(presets);
                showHideCustomEthnicityPanel()

                // show the presets (step 2) and table type (step 3) section
                document.getElementById('ethnicity_settings_section').classList.remove('hidden')

                if (getIsSimpleData(table_data)) {
                    document.getElementById('complex_table_options').classList.add('hidden')
                } else {
                    document.getElementById('complex_table_options').classList.remove('hidden')
                }

                // any further processing
                if (on_success) {
                    on_success();
                }
            },
            failure: function () {
                console.log('failed to get ethnicity classifications');
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
        var listWithNone = dropdownHtmlWithDefault(headers, 'none', '[None]');
        var listWithSquareNone = dropdownHtmlWithDefault(headers, '[None]', '[None]');
        var listWithRequired = dropdownHtmlWithDefault(headers, unselectedOptionString, unselectedOptionString);

        $('#ethnicity-as-row__columns').html(listWithRequired);
        $('#ethnicity-as-row__column-order').html(listWithRequired);
        $('#ethnicity-as-column__rows').html(listWithRequired);
        $('#ethnicity-as-column__row-order').html(listWithRequired);

        $('#table_column_1').html(listWithRequired);
        $('#table_column_2').html(listWithNone);
        $('#table_column_3').html(listWithNone);
        $('#table_column_4').html(listWithNone);
        $('#table_column_5').html(listWithNone);

        $('#index_column_name').val('Ethnicity')
    }

    function selectDropdown(dropdown_id, value) {
        var dropdown = document.getElementById(dropdown_id);
        for (var i = 0; i < dropdown.length; i++) {
            dropdown[i].selected = (dropdown[i].value === value)
        }
    }

    function showHideCustomEthnicityPanel() {
        if ($('#ethnicity_settings').val() === 'custom') {
            document.getElementById('custom_classification__panel').classList.remove('hidden')
        } else {
            document.getElementById('custom_classification__panel').classList.add('hidden')
        }
    }

    function populateEthnicityPresets(presets) {
        var html = '';
        for (var p in presets) {
            var preset_name = presets[p]['preset']['name'];
            var preset_id = presets[p]['preset']['id'];
            if (p === 0) {
                html = html + '<option value="' + preset_id + '" selected>' + preset_name + '</option>';
            } else {
                html = html + '<option value="' + preset_id + '" >' + preset_name + '</option>';
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

    function dropdownHtmlWithDefault(headers, defaultValue, defaultLabel) {
        var html = '<option value="' + defaultValue + '" selected>' + defaultLabel + '</option>';
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

    function dataColumnChange(evt) {
        var selected_column_name = $('#' + this.id + ' option:selected').val();

        var new_column_name = (selected_column_name === unselectedOptionString) ? "" : selected_column_name;

        $('#' + this.id + '_name').val(new_column_name);

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
        if (tipsOfType(tips, RECTANGLE_ERROR).length > 0) {
            document.getElementById('errors_container').classList.remove('hidden')
            document.getElementById('tip__rectangular-data').classList.remove('hidden')
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

    function displayTable() {
        document.getElementById('tips_container').classList.add('hidden')
        document.getElementById('preview_container').classList.remove('hidden')

        var tableObject = innerBuildTableObject();
        if (tableObject) {
            if (tableObject.title && tableObject.title.text) {
                $('#title-container').html('<h3 class="heading-small">' + tableObject.title.text + '</h3>');
            }
            tableObject.title = '';
            drawTable('container', tableObject);

            document.getElementById('save_section').classList.remove('hidden')
        }
        document.getElementById('table_title').dispatchEvent(new Event("input"));
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
                data: JSON.stringify({
                    'tableObject': tableObject, 'source': src, 'tableBuilderVersion': 2,
                    'classificationCode': getPresetCode(),
                    'customClassificationCode': getCustomClassificationCode(),
                    'customClassification': getCustomObject(),
                    'ethnicityValues': getEthnicityValues(table_data)
                }),
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
            'custom': getCustomObject(),
            'tableOptions': getTableTypeOptions(),
            'tableValues': getTableValues(),
            'version': '2.0'
        }
    }

    function getTableTypeOptions() {
        if (getIsSimpleData(table_data)) {
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
            'table_index_column_name': $('#index_column_name').val(),
        }
    }

    function getPresetCode() {
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

    function notNullOrNone(val) {  // We ingest some weird/inconsistent data from table builder v1 so this check helps prevent errors.
        return val !== null & val != 'none'
    }

    function buildTableColumns() {
        var columns = []
        $('.column_option_picker').each(function (idx) {
            if (notNullOrNone($(this).val())) {
                columns.push($(this).val());
            }
            ;
        });
        return columns
    }

    function buildEthnicityByRowColumns() {
        var columns = [$('#ethnicity-as-row__columns').val()]
        if (notNullOrNone($('#ethnicity-as-row__column-order').val())) {
            columns.push($('#ethnicity-as-row__column-order').val())
        }
        return columns
    }

    function buildEthnicityByColumnColumns() {
        var columns = [$('#ethnicity-as-column__rows').val()]
        if (notNullOrNone($('#ethnicity-as-column__row-order').val())) {
            columns.push($('#ethnicity-as-column__row-order').val())
        }
        return columns
    }

    // This function examines the HTML page and returns an array of headings for columns
    // being used.
    //
    // Note that a column may have no header, and that this is represented by a empty string,
    // eg ['']. This is important as the length of this array is also used to determine the
    // number of columns in use.
    function buildTableColumnNames() {
        var columns = []

        $('.column_option_picker').each(function (index) {

            if ($(this).val() !== 'none') {
                columns.push($('.column_option_picker_name')[index].value)
            }

        })

        return columns
    }


    function innerBuildTableObject() {
        var tableObject = null;
        var preset = getPresetWithId($('#ethnicity_settings').val());
        if (getIsSimpleData(table_data)) {
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
                $('#index_column_name').val(),
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
                    $('#index_column_name').val(),
                    $('#ethnicity-as-row__column-order').val());
            } else {
                var all_table_columns = buildTableColumns().concat(buildEthnicityByColumnColumns());
                tableObject = buildTableObject(buildDataWithPreset(preset, table_data, all_table_columns),
                    $('#table_title').val(),
                    '',
                    '',
                    $('#ethnicity-as-column__rows').val(),
                    '',
                    'Ethnicity',
                    $('#ethnicity-as-column__row-order').val(),
                    buildTableColumns(),
                    buildTableColumnNames(),
                    $('#index_column_name').val(),
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

    function getPresetWithId(preset_id) {
        for (p in presets) {
            if (presets[p].preset.id === preset_id) {
                return presets[p];
            }
        }
        return null;
    }


    /*
        EVENT HANDLERS
    */
    // Switch TABLE_OPTIONS panels
    $('#ethnicity_settings').change(function() {
        showHideCustomEthnicityPanel()
        preview()
    });
    $('#custom_classification__selector').change(preview);

    function selectPreset(preset) {
        $('#ethnicity_settings').val(preset);
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
        TABLE PANEL events
    */

    // COMPLEX TABLE events
    $('#complex-table__data-style').change(function () {
        selectDataStyle();
        modifyIndexColumnNameAndPreview();
    });
    $('#ethnicity-as-row__columns').change(function () {
        setColumnOrdering();
        modifyIndexColumnNameAndPreview();
    });
    $('#ethnicity-as-row__column-order').change(preview);
    $('#ethnicity-as-column__rows').change(function () {
        setRowOrdering();
        modifyIndexColumnNameAndPreview();
    });
    $('#ethnicity-as-column__row-order').change(preview);

    $('#grouped-bar__bar_order').change(preview);
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

    $('#index_column_name').change(preview);

    function selectDataStyle() {
        if ($('#complex-table__data-style').val() === "ethnicity_as_row") {
            document.getElementById('complex-table__ethnicity-is-row').classList.remove('hidden')
            document.getElementById('complex-table__ethnicity-is-column').classList.add('hidden')
        } else {
            document.getElementById('complex-table__ethnicity-is-row').classList.add('hidden')
            document.getElementById('complex-table__ethnicity-is-column').classList.remove('hidden')
        }
    }


    // Show-hide NUMBER-FORMAT__OTHER panel
    $('#number_format').change(function () {
        if ($(this).val() === 'other') {
            document.getElementById('other_number_format').classList.remove('hidden')
        } else {
            document.getElementById('other_number_format').classList.add('hidden')
        }
        preview();
    });

    function modifyIndexColumnNameAndPreview(evt) {
        var indexColumnName = $('#index_column_name').val()
        var headers = table_data[0]

        // If index_column_name has not been modified change if possible
        if (headers.indexOf(indexColumnName) >= 0 || indexColumnName === unselectedOptionString) {
            if ($('#complex-table__data-style').val() === "ethnicity_as_column") {
                $('#index_column_name').val($('#ethnicity-as-column__rows').val())
            } else {
                $('#index_column_name').val('Ethnicity')
            }
        }

        preview(evt)
    }

    function setRowOrdering(evt) {
        $('#ethnicity-as-column__row-order').val($('#ethnicity-as-column__rows').val())
    }

    function setColumnOrdering(evt) {
        $('#ethnicity-as-row__column-order').val($('#ethnicity-as-row__columns').val())
    }

    function initialiseForm() {
        if (settings.data) {
            var data_text = _.map(settings.data, function (d) {
                return d.join('\t')
            }).join('\n');
            $('#data_text_area').val(data_text);

            handleNewData(function () {
                document.getElementById('data-panel').classList.add('hidden')
                document.getElementById('edit-panel').classList.remove('hidden')
                setupTablebuilderWithSettings(settings);
                preview()
            })
        }
    };

    function setupTablebuilderWithSettings(settings) {
        if (settings.preset) {
            selectPreset(settings.preset);
        }
        if (settings.custom) {
            selectCustomValues(settings.custom)
        }

        showHideCustomEthnicityPanel()

        $('#table_title').val(settings.tableValues.table_title);
        document.getElementById('table_title').dispatchEvent(new Event("input"));

        $('#complex-table__data-style').val(settings.tableOptions.data_style);

        /*
        If a table has no explicit row ordering, there are some circumstances in which the live table can have data cells
        transposed - resulting in an inaccurate table. We will prevent this by enforcing an explicit row order. If one
        hasn't been provided previously, we'll assume the table should be sorted (alphabetically) by the current
        row/column selection.
        https://trello.com/c/mrtsskDU/1103
        */
        if (settings.tableOptions.order == NONE_VALUE) {
            settings.tableOptions.order = settings.tableOptions.selection
        }

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

        $('#index_column_name').val(settings.tableValues.table_index_column_name);
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
        return {'multiplier': 1.0, 'prefix': '', 'suffix': '', 'min': '', 'max': ''}
    } else if (format === 'percent') {
        return {'multiplier': 1.0, 'prefix': '', 'suffix': '%', 'min': 0.0, 'max': 100.0}
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
    var ethnicityColumn = getEthnicityColumnHeader();
    var secondaryColumn = getSecondaryColumnHeader();

    var dataErrors = validateData(table_data, ethnicityColumn, secondaryColumn);
    return dataErrors;
}

var MISSING_FIELD_ERROR = 'Missing field error';

function checkRequiredFields() {
    if ($('#ethnicity_settings').val() === 'custom' && $('#custom_classification__selector').val() === 'Please select') {
        return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'custom_classification__selector' }]
    }

    if (getIsSimpleData(table_data) === false) {
        if ($('#complex-table__data-style').val() === 'ethnicity_as_row') {
            if ($('#ethnicity-as-row__columns').val() === unselectedOptionString) {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-row__columns' }]
            };
            if ($('#ethnicity-as-row__column-order').val() === unselectedOptionString) {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-row__column-order' }]
            };
        } else {
            if ($('#ethnicity-as-column__rows').val() === unselectedOptionString) {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-column__rows' }]
            };
            if ($('#ethnicity-as-column__row-order').val() === unselectedOptionString) {
                return [{ 'errorType': MISSING_FIELD_ERROR, 'field': 'ethnicity-as-column__row-order' }]
            };
        }
    }

    if ($('#table_column_1').val() === unselectedOptionString) {
        return [{'errorType': MISSING_FIELD_ERROR, 'field': 'table_column_1'}]
    }

    return [];
}

function getEthnicityColumnHeader() {
    for (var i in table_data[0]) {
        var lower = table_data[0][i].toLowerCase();
        if (lower.search('ethnic') >= 0) {
            return table_data[0][i]
        }
    }
    return null
}

function getSecondaryColumnHeader() {
    if (getIsSimpleData(table_data)) {
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
