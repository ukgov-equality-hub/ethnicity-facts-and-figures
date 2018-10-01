
/*
  Accordion

  This allows a collection of sections to be collapsed by default,
  showing only their headers. Sections can be exanded or collapsed
  individually by clicking their headers. An "Open all" button is
  also added to the top of the accordion, which switches to "Close all"
  when all the sections are expanded.

  The state of each section is saved to the DOM via the `aria-expanded`
  attribute, which also provides accessibility.

*/

function Accordion (element) {
  // First do feature detection for required API methods
  if (
    document.querySelectorAll &&
    window.NodeList &&
    'classList' in document.body
  ) {
    this.element = element
    this.sections = []
  }
}

function AccordionSection (element, accordion) {
  this.element = element
  this.accordion = accordion
}

Accordion.prototype.setup = function () {
  var accordionSections = this.element.querySelectorAll('.accordion-section')

  var accordion = this

  for (var i = accordionSections.length - 1; i >= 0; i--) {

    var accordionSection = new AccordionSection(accordionSections[i], accordion)
    accordionSection.setup()

    accordion.sections.push(accordionSection)
  };

  var accordionControls = document.createElement('div')
  accordionControls.setAttribute('class', 'accordion-controls')

  var openOrCloseAllButton = document.createElement('button')
  openOrCloseAllButton.textContent = 'Open all'
  openOrCloseAllButton.setAttribute('class', 'accordion-expand-all')
  openOrCloseAllButton.setAttribute('aria-expanded', 'false')

  openOrCloseAllButton.setAttribute('data-on', 'click')
  openOrCloseAllButton.setAttribute('data-event-category', 'Accordion')
  openOrCloseAllButton.setAttribute('data-event-action', 'All opened')

  openOrCloseAllButton.addEventListener('click', this.openOrCloseAll.bind(this))

  accordionControls.appendChild(openOrCloseAllButton)

  this.element.insertBefore(accordionControls, this.element.firstChild)
  this.element.classList.add('with-js')
}

Accordion.prototype.openOrCloseAll = function (event) {
  var openOrCloseAllButton = event.target
  var nowExpanded = !(openOrCloseAllButton.getAttribute('aria-expanded') === 'true')

  var eventAction = nowExpanded ? 'All closed' : 'All opened'
  openOrCloseAllButton.setAttribute('data-event-action', eventAction)

  for (var i = this.sections.length - 1; i >= 0; i--) {
    this.sections[i].setExpanded(nowExpanded)
  };

  this.setOpenCloseButtonExpanded(nowExpanded)
}

Accordion.prototype.setOpenCloseButtonExpanded = function (expanded) {
  var openOrCloseAllButton = this.element.querySelector('.accordion-expand-all')

  var newButtonText = expanded ? 'Close all' : 'Open all'
  openOrCloseAllButton.setAttribute('aria-expanded', expanded)
  openOrCloseAllButton.textContent = newButtonText
}

Accordion.prototype.updateOpenAll = function () {
  var sectionsCount = this.sections.length

  var openSectionsCount = 0

  for (var i = this.sections.length - 1; i >= 0; i--) {
    if (this.sections[i].expanded()) {
      openSectionsCount += 1
    }
  };

  if (sectionsCount === openSectionsCount) {
    this.setOpenCloseButtonExpanded(true)
  } else {
    this.setOpenCloseButtonExpanded(false)
  }
}

AccordionSection.prototype.setup = function () {
  this.element.setAttribute('aria-expanded', 'false')

  this.header = this.element.querySelector('.accordion-section-header')
  this.header.addEventListener('click', this.toggleExpanded.bind(this))

  var icon = document.createElement('span')
  icon.setAttribute('class', 'icon')

  this.header.appendChild(icon)
}

AccordionSection.prototype.toggleExpanded = function () {
  var expanded = (this.element.getAttribute('aria-expanded') === 'true')

  this.setExpanded(!expanded)
  this.accordion.updateOpenAll()
}

AccordionSection.prototype.expanded = function () {
  return (this.element.getAttribute('aria-expanded') === 'true')
}

AccordionSection.prototype.setExpanded = function (expanded) {
  this.element.setAttribute('aria-expanded', expanded)

  var eventAction = (expanded ? 'Section closed' : 'Section opened')

  this.header.setAttribute('data-event-action', eventAction)

  // This is set to trigger reflow for IE8, which doesn't
  // always reflow after a setAttribute call.
  this.element.className = this.element.className
}

if (
  'addEventListener' in document &&
  document.querySelectorAll
) {
  document.addEventListener('DOMContentLoaded', function () {
    var accordions = document.querySelectorAll('.accordion')

    for (var i = accordions.length - 1; i >= 0; i--) {
      var accordion = new Accordion(accordions[i])
      accordion.setup()
    };
  })
}
