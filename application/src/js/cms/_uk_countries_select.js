

function ukCountriesSelect(element) {

  this.element = element;

  var countryInputs, ukInput;
  setup();

  function setup() {

    if (!(
      this.element &&
      'querySelector' in this.element &&
      'querySelectorAll' in this.element
    )) { return; }

    ukInput = document.createElement('input')
    ukInput.setAttribute('class', 'govuk-checkboxes__input')
    ukInput.setAttribute('type', 'checkbox')
    ukInput.setAttribute('id', 'uk')

    var ukInputLabel = document.createElement('label')
    ukInputLabel.setAttribute('class', 'govuk-label govuk-checkboxes__label')
    ukInputLabel.setAttribute('for', 'uk')
    ukInputLabel.textContent = 'United Kingdom'

    var ukInputContainer = document.createElement('div')
    ukInputContainer.setAttribute('class', 'govuk-checkboxes__item uk')

    ukInputContainer.appendChild(ukInput)
    ukInputContainer.appendChild(ukInputLabel)

    var legend = this.element.querySelector('legend')

    if (!legend) {
      console.warn('missing legend for UK fieldset');
      return;
    }

    var overseasNode = Array.prototype.slice.apply(
                          document.querySelectorAll('.govuk-checkboxes .govuk-checkboxes__item'))
                                      .filter(function (x){
                                        return x.textContent.match("Overseas")
                                      })[0];

    this.element.querySelector('.govuk-checkboxes').insertBefore(ukInputContainer, overseasNode);

    if (ukInput) {
      ukInput.addEventListener('change', ukChanged)

      countryInputs = this.element.querySelectorAll('input.country')

      for (var i = countryInputs.length - 1; i >= 0; i--) {
        countryInputs[i].addEventListener('change', countryChanged)
      }

      countryChanged();

    }

  }

  function countryChanged(event) {

    var checkedCountries = 0;

    for (var i = countryInputs.length - 1; i >= 0; i--) {

      if (countryInputs[i].checked) {
        checkedCountries += 1;
      }

    }
    // Modified for Overseas
    ukInput.checked = (checkedCountries == countryInputs.length-1);

  }

  function ukChanged() {
    for (var i = countryInputs.length - 1; i >= 0; i--) {
      if( countryInputs[i].value !== "OVERSEAS" )
        countryInputs[i].checked = ukInput.checked;
    }

  }

}
