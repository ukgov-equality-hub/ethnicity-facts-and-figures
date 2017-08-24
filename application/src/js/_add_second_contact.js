
/* Second contact details

  This hides a set of 'second contact' fields behind
  a link, unless the fields already contain values.

*/

function SecondContactDetails(fieldset) {

  // First do feature detection for required API methods
  if (
    document.querySelectorAll &&
    window.NodeList &&
    'classList' in document.body
  ) {
    this.fieldset = fieldset
    this.setup()
  }
}

SecondContactDetails.prototype.setup = function() {
  this.fieldset.classList.add('hidden')

  this.add_second_contact_button = document.createElement('button')
  this.add_second_contact_button.classList.add('link')
  this.add_second_contact_button.textContent = 'Add second contact'
  this.add_second_contact_button.addEventListener('click', this.expandFieldset.bind(this))

  var parent = this.fieldset.parentElement

  parent.insertBefore(this.add_second_contact_button, this.fieldset)

};

SecondContactDetails.prototype.expandFieldset = function() {
  this.add_second_contact_button.remove()
  this.fieldset.classList.remove('hidden')
};

if (
  'addEventListener' in document &&
  document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {
    var second_contact_details = document.querySelectorAll('.js-second-contact-details')

    for (var i = second_contact_details.length - 1; i >= 0; i--) {
      new SecondContactDetails(second_contact_details[i])
    };

  })

}