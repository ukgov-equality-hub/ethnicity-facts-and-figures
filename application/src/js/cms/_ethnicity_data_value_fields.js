
function ethnicityDataValueFields (fieldset) {
  var fieldset = fieldset

  if (
    'querySelector' in document &&
    'addEventListener' in document &&
    Function.prototype.bind
  ) {
    var ethnicityCategorisationSelect, broadValuesCheckbox
    setup()
  }

  function setup () {
    if (fieldset) {
      ethnicityCategorisationSelect = fieldset.querySelector('select.ethnicity-categorisation')
      broadValuesCheckbox = fieldset.querySelector('input.broad-values')

      if (ethnicityCategorisationSelect && broadValuesCheckbox) {
        ethnicityCategorisationSelect.addEventListener('change', selectChanged.bind(this))
        updateBroadValuesCheckboxStatus()
      }
    }
  }

  function updateBroadValuesCheckboxStatus () {
    var selectedOption = ethnicityCategorisationSelect.selectedOptions[0]

    if (selectedOption.getAttribute('data-parents') == 'true') {
      broadValuesCheckbox.removeAttribute('disabled')
    } else {
      broadValuesCheckbox.checked = false
      broadValuesCheckbox.setAttribute('disabled', 'disabled')
    }
  }

  function selectChanged () {
    updateBroadValuesCheckboxStatus()
  }
}
