

function ukCountriesSelect(element) {

  this.element = element;

  UKCountries = ['ENGLAND', 'WALES', 'SCOTLAND', 'NORTHERN_IRELAND'];
  Overseas = 'OVERSEAS';

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
    checkedCountries = Array.prototype.slice.apply(countryInputs).filter(function (x){
      return x.checked && x.value != Overseas;
    }).map(function (x){
      return x.value;
    });

    ukInput.checked = UKCountries.filter(function (x){
      return !(checkedCountries.indexOf(x) > -1);
    }).length === 0;
  }

  function ukChanged() {
    for (var i = countryInputs.length - 1; i >= 0; i--) {
      if( countryInputs[i].value !== "OVERSEAS" )
        countryInputs[i].checked = ukInput.checked;
    }

  }

}
