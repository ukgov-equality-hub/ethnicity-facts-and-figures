/* Secondary Sources

  This hides "Secondary Source" fields (unless they contain values)
  behind an "Add secondary source" link.

*/

function SecondarySources (element) {
  function setup () {
    var secondarySources = that.element.querySelectorAll('.source')

    for (var i = 0; i < secondarySources.length; i++) {
      that.secondarySources.push(new SecondarySource(secondarySources[i], that))
    };

    that.showButtonForFirstHiddenSource()
  }

  this.element = element
  this.secondarySources = []

  var that = this
  setup()
}

function SecondarySource (fieldset, secondarySources) {
  function setup () {
    var checkedFieldTypes = ['radio', 'checkbox']
    var ignorableFieldTypes = ['submit', 'hidden', 'button']

    var fields = that.fieldset.querySelectorAll('input, textarea')
    var anyFieldsHaveValue = false

    for (var i = fields.length - 1; i >= 0; i--) {
      if (
        (checkedFieldTypes.includes(fields[i].type) && fields[i].checked === true) ||
        (!checkedFieldTypes.includes(fields[i].type) && !ignorableFieldTypes.includes(fields[i].type) && fields[i].value !== '')
      ) {
        anyFieldsHaveValue = true
        break
      }
    };

    that.add_secondary_source_button = document.createElement('button')
    that.add_secondary_source_button.classList.add('link')
    that.add_secondary_source_button.classList.add('hidden')
    that.add_secondary_source_button.textContent = 'Add secondary source'
    that.add_secondary_source_button.addEventListener('click', that.addSourceButtonClicked.bind(that))
    var parent = that.fieldset.parentElement
    parent.insertBefore(that.add_secondary_source_button, that.fieldset)

    var removeSecondarySourceButton = document.createElement('button')
    removeSecondarySourceButton.classList.add('delete')
    removeSecondarySourceButton.classList.add('link')
    removeSecondarySourceButton.textContent = 'Remove source'
    removeSecondarySourceButton.addEventListener('click', that.removeSourceButtonClicked.bind(that))

    var legend = that.fieldset.querySelector('legend')

    if (legend) {
      that.fieldset.insertBefore(removeSecondarySourceButton, legend.nextSibling)
    }

    that.setHidden(!anyFieldsHaveValue)
  }

  this.fieldset = fieldset
  this.secondarySources = secondarySources
  this.hidden = false

  var that = this
  setup()
}

SecondarySources.prototype.showButtonForFirstHiddenSource = function () {
  if (this.secondarySources.length > 0) {
    var firstHiddenSourceShown = false

    for (var i = 0; i < this.secondarySources.length; i++) {
      if (this.secondarySources[i].hidden && firstHiddenSourceShown === false) {
        this.secondarySources[i].showAddSourceButton(true)
        firstHiddenSourceShown = true
      } else {
        this.secondarySources[i].showAddSourceButton(false)
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

  this.secondarySources.showButtonForFirstHiddenSource()
}

SecondarySource.prototype.showAddSourceButton = function (show) {
  if (show) {
    this.add_secondary_source_button.classList.remove('hidden')
  } else {
    this.add_secondary_source_button.classList.add('hidden')
  }
}

SecondarySource.prototype.addSourceButtonClicked = function (event) {
  this.setHidden(false)
  event.preventDefault()
}

SecondarySource.prototype.removeSourceButtonClicked = function (event) {
  var fields = this.fieldset.querySelectorAll('input, textarea, option')

  for (var i = 0; i < fields.length; i++) {
    fields[i].value = ''
    fields[i].removeAttribute('checked')
    fields[i].removeAttribute('selected')
  };

  this.setHidden(true)
  event.preventDefault()
}

SecondarySources.prototype.setup = function () {
  // TODO: move setup here.
}

if (
  'addEventListener' in document &&
  document.querySelectorAll
) {
  document.addEventListener('DOMContentLoaded', function () {
    var secondarySources = document.querySelectorAll('.js-secondary-sources')

    for (var i = secondarySources.length - 1; i >= 0; i--) {
      new SecondarySources(secondarySources[i]).setup()
    };
  })
}
