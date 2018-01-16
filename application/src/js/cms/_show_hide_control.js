
/* Show or Hide content controlled by a Radio button or Checkbox */
function showHideControl(element) {

  if (
      document.querySelectorAll &&
      Function.prototype.bind &&
      ('classList' in document.createElement('_'))
    ) {

    var element = element;
    var elementControlled = null;
    setup()

  }

  function setup() {

    var elementControlledId = element.getAttribute('aria-controls')
    var elementName = element.getAttribute('name');

    if (elementControlledId) {
      elementControlled = document.getElementById(elementControlledId);
    }

    if (elementControlled) {

      var allRadioButtonsInSameGroup = document.querySelectorAll('input[name=' + elementName + ']');

      for (radioButton of allRadioButtonsInSameGroup) {
        radioButton.addEventListener('change', inputChanged.bind(this));
      }

    }

    expandOrCollapseTarget(element.checked)
  }

  function expandOrCollapseTarget(expand) {
    if (expand) {
      elementControlled.classList.remove('js-hidden');
    } else {
      elementControlled.classList.add('js-hidden');
    }
  }

  function inputChanged(event) {
    expandOrCollapseTarget(element.checked);
    element.setAttribute('aria-expanded', element.checked);
  }

}
