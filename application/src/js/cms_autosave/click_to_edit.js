// Functions to enable click-to-edit fields
    function PreviewAndEditSection(element) {

        var element = element;
        var preview, edit, text_inputs, text_area, checkboxesAndRadios
        setup();

        function setup() {

            preview = element.querySelector('.preview');
            edit = element.querySelector('.edit');
            text_inputs = edit.querySelectorAll('input[type=text]:not(.js-dependent), input[type=url]:not(.js-dependent)');
            text_area = edit.querySelector('textarea');

            checkboxesAndRadios = edit.querySelectorAll('input[type=checkbox], input[type=radio]')

            radioButtons = edit.querySelectorAll('input[type=radio]')

           preview.addEventListener('click', previewClicked);
           preview.addEventListener('keyup', previewKeyedUp);

            if (text_inputs.length == 1) {
                text_inputs[0].addEventListener('blur', inputBlurred);
                text_inputs[0].addEventListener('keyup', enterKeyPressed);
            }

            if (text_area) {
                text_area.addEventListener('blur', inputBlurred);
            }


            var cancel = edit.querySelector('.cancel')
            if (cancel) {
                cancel.addEventListener('click', cancelClicked);
            }

            var save = edit.querySelector('.save')
            if (save) {
                save.addEventListener('click', saveAndPreview);
            }
        }

        function inputBlurred(event) {

            if (!edit.classList.contains('hidden') && !event.target.classList.contains('js-dependent')) {
                saveAndPreview(event);
            }
        }

        function cancelClicked(event) {

            showPreview();

            if (text_inputs[0]) {
                if (preview.classList.contains('empty')) {
                    text_inputs[0].value = '';
                } else {
                    text_inputs[0].value = preview.textContent;
                }
            }

            event.preventDefault()
        }

        function enterKeyPressed(event) {
            if (event.keyCode == 13) {
                saveAndPreview(event);
            }
        }

        function saveAndPreview(event) {

            var displayText;

            /* TODO: MAKE CALL TO SAVE THE UPDATED FIELD */
            if (text_inputs[0]) {
                displayText = text_inputs[0].value.trim();
            }
            else if (text_area) {
                displayText = text_area.value.trim();

                if (text_area.classList.contains('for-bullets')) {
                    preview.innerHTML = displayText.replace(/^\*\s/gm, "<li>").replace(/\n/g, '</li>');
                } else if (text_area.classList.contains('for-paragraphs')) {
                    preview.innerHTML = displayText.replace(/\n/g, "<br>").replace(/\n/g, '</li>');
                }
            }

            else if (checkboxesAndRadios.length > 0) {

                var checkedLabels = []

                for (var i = 0; i < checkboxesAndRadios.length; i++) {

                    if (checkboxesAndRadios[i].checked) {

                        var fieldId = checkboxesAndRadios[i].getAttribute('id')
                        var associatedLabel = document.querySelector('label[for=' + fieldId + ']')

                        if (associatedLabel) {
                            checkedLabels.push(associatedLabel.textContent)
                        } else {
                            console.warn('Missing label for checkbox with ID ' + fieldId)
                        }
                    }
                }

                if (checkedLabels.length > 0) {

                    displayText = checkedLabels.join(', ')

                }

            }


            /* override the display text from the data attribute if it exists */
            if (displayText && preview.getAttribute('data-preview-text')) {
                displayText = preview.getAttribute('data-preview-text')
            }

            if (displayText && displayText != '') {

                preview.textContent = displayText
                preview.classList.remove('empty')

            } else {

                preview.classList.add('empty');
                preview.textContent = preview.getAttribute('data-empty-text');

            }

            showPreview();
            event.preventDefault()
        }

        function previewKeyedUp(event) {
            if (event.keyCode == 13) {
                showEdit();
            }
        }

        function previewClicked(event) {
            showEdit();
        }

        function showEdit() {
            preview.classList.toggle('hidden');
            edit.classList.toggle('hidden');
            if (text_inputs[0]) {
                text_inputs[0].focus();
            }
            if (text_area) {
                text_area.focus();
            }
        }

        function showPreview() {
            edit.classList.add('hidden');
            preview.classList.remove('hidden');
        }
    }

    function setupAutosave() {

        var previewAndEditSections = document.querySelectorAll('.preview-and-edit');

        for (var i = 0; i < previewAndEditSections.length; i++) {
            new PreviewAndEditSection(previewAndEditSections[i]);
        }

    }

    document.addEventListener('DOMContentLoaded', setupAutosave);
