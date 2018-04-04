// Function for making table rows reorerable.
//
// Initialise with a reference to a table element, eg
//
//   new ReorderableRows(document.querySelector('table'));
//
// To be notified when a row was dropped, assign a function
// reference to the the onDrop property, eg:
//
//   var r = new ReorderableRows(document.querySelector('table'));
//   r.onDrop = function() {
//      console.log('moved');
//   }

var ReorderableRows = function(element) {

  var element = element;

  var elementBeingDragged = null;
  this.onDrop = null;
  var elementBeingDragged;
  setup();


  function setup() {

    // TODO: Feature detection for the drag-drop API
    element.classList.add('reorderable')

    var rows = element.querySelectorAll('tbody tr')

    for (var i = 0; i < rows.length; i++) {
      rows[i].draggable = true
    }

  }

  var dragStarted = function(event) {

    event.dataTransfer.effectAllowed = 'move';
    elementBeingDragged = event.target;

    while (elementBeingDragged.tagName != 'TR') {
      elementBeingDragged = elementBeingDragged.parentElement
    }

    elementBeingDragged.classList.add('being-dragged')

    event.dataTransfer.setData('text/html', elementBeingDragged.innerHTML)

  }

  var dropped = function(event) {
    measureTarget = event.target;

    while (measureTarget.tagName != 'TR') {
      measureTarget = measureTarget.parentElement
    }

    if (measureTarget.classList.contains('drop-destination-above')) {
      measureTarget.parentElement.insertBefore(elementBeingDragged, measureTarget);
    } else {
      measureTarget.parentElement.insertBefore(elementBeingDragged, measureTarget.nextSibling);
    }

    document.querySelectorAll('.drop-destination-above').forEach(function(el){
       el.classList.remove('drop-destination-above');
    })

    document.querySelectorAll('.drop-destination-below').forEach(function(el){
       el.classList.remove('drop-destination-below');
    })

    document.querySelectorAll('.being-dragged').forEach(function(el){
       el.classList.remove('being-dragged');
    })

    if (this.onDrop) {
      this.onDrop(element)
    }
  }


  var draggedOver = function(event) {

    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'

    var measureTarget = event.target

    while (measureTarget.tagName != 'TR') {
      measureTarget = measureTarget.parentElement
    }

    document.querySelectorAll('.drop-destination-above').forEach(function(el){
      el.classList.remove('drop-destination-above');
    })

    document.querySelectorAll('.drop-destination-below').forEach(function(el){
      el.classList.remove('drop-destination-below');
    })

    if (measureTarget != elementBeingDragged) {

      if (event.offsetY < (measureTarget.clientHeight / 2)) {
        measureTarget.classList.add('drop-destination-above')
      } else {
        measureTarget.classList.add('drop-destination-below')
      }
    }

  }

  element.addEventListener('dragstart', dragStarted.bind(this));
  element.addEventListener('drop', dropped.bind(this));
  element.addEventListener('dragover', draggedOver.bind(this));

}
