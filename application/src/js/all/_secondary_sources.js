/* Secondary Sources

  This hides "Secondary Source" fields (unless they contain values)
  behind an "Add secondary source" link.

*/


function SecondarySources(element) {

  function setup() {
    var secondary_sources = that.element.querySelectorAll('.source')


    for (var i = 0; i < secondary_sources.length; i++) {
      that.secondary_sources.push(new SecondarySource(secondary_sources[i], that))
    };

    that.showButtonForFirstHiddenSource()

  }

  this.element = element
  this.secondary_sources = []

  var that = this
  setup()


}

function SecondarySource(fieldset, secondary_sources) {

  function setup() {

    var checkedFieldTypes = ['radio', 'checkbox'];
    var ignorableFieldTypes = ['submit', 'hidden', 'button'];

    var fields = that.fieldset.querySelectorAll('input, textarea')
    var anyFieldsHaveValue = false;

    for (var i = fields.length - 1; i >= 0; i--) {

      if (
        (checkedFieldTypes.includes(fields[i].type) && fields[i].checked === true) ||
        (!checkedFieldTypes.includes(fields[i].type) && !ignorableFieldTypes.includes(fields[i].type) && fields[i].value != "")
      ) {

        anyFieldsHaveValue = true
        break;
      }
    };

    that.add_secondary_source_button = document.createElement('a')
    that.add_secondary_source_button.classList.add('govuk-link')
    that.add_secondary_source_button.classList.add('eff-link__secondary-source')
    that.add_secondary_source_button.classList.add('hidden')
    that.add_secondary_source_button.href = '#'
    that.add_secondary_source_button.textContent = 'Add secondary source'
    that.add_secondary_source_button.addEventListener('click', that.addSourceButtonClicked.bind(that))
    var parent = that.fieldset.parentElement
    parent.insertBefore(that.add_secondary_source_button, that.fieldset)


    var remove_secondary_source_button = document.createElement('a')
    remove_secondary_source_button.classList.add('govuk-link')
    remove_secondary_source_button.classList.add('eff-link__secondary-source')
    remove_secondary_source_button.classList.add('eff-link__secondary-source--delete')
    remove_secondary_source_button.href = '#'
    remove_secondary_source_button.textContent = 'Remove source'
    remove_secondary_source_button.addEventListener('click', that.removeSourceButtonClicked.bind(that))

    var legend = that.fieldset.querySelector('legend')

    if (legend) {
      that.fieldset.insertBefore(remove_secondary_source_button, legend.nextSibling)
    }

    that.setHidden(!anyFieldsHaveValue)

  }


  this.fieldset = fieldset
  this.secondary_sources = secondary_sources
  this.hidden = false

  var that = this
  setup()
}



SecondarySources.prototype.showButtonForFirstHiddenSource = function () {

  if (this.secondary_sources.length > 0) {

    var firstHiddenSourceShown = false

    for (var i = 0; i < this.secondary_sources.length; i++) {

      if (this.secondary_sources[i].hidden && firstHiddenSourceShown == false) {
        this.secondary_sources[i].showAddSourceButton(true)
        firstHiddenSourceShown = true
      } else {
        this.secondary_sources[i].showAddSourceButton(false)
      }

    };

  }

}


SecondarySource.prototype.setHidden = function (hidden) {
  this.hidden = hidden

  if (hidden) {
    this.fieldset.classList.add('hidden')
  } else {
    this.fieldset.classList.remove('hidden')
  }

  this.secondary_sources.showButtonForFirstHiddenSource()
}

SecondarySource.prototype.showAddSourceButton = function (show) {

  if (show) {
    this.add_secondary_source_button.classList.remove('hidden')
  } else {
    this.add_secondary_source_button.classList.add('hidden')
  }

}


SecondarySource.prototype.addSourceButtonClicked = function (event) {
  event.preventDefault()

  // `remove_data_source` hooks into the application.cms.forms.DataSourceForm field.
  this.fieldset.querySelector('.js-remove-data-source input').checked = false;

  this.setHidden(false)
};

SecondarySource.prototype.removeSourceButtonClicked = function (event) {
  event.preventDefault()

  this.setHidden(true)

  // `remove_data_source` hooks into the application.cms.forms.DataSourceForm field.
  this.fieldset.querySelector('.js-remove-data-source input').checked = true;
};

if (
  'addEventListener' in document &&
  document.querySelectorAll
) {

  document.addEventListener('DOMContentLoaded', function () {
    var secondary_sources = document.querySelectorAll('.js-secondary-sources')

    for (var i = secondary_sources.length - 1; i >= 0; i--) {
      new SecondarySources(secondary_sources[i])
    };

  })

}
