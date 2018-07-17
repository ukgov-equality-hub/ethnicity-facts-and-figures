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

  setup();


  function setup() {
    // TODO: Feature detection for the drag-drop API
    element.classList.add('reorderable')
    var rows = element.querySelectorAll('tbody tr')
    for (var i = 0; i < rows.length; i++) {
      rows[i].draggable = true
    }
  }

  var dragEnded = function(evt) {
    elementBeingDragged = null;

    document.querySelectorAll('.being-dragged').forEach(function(el) {
       el.classList.remove('being-dragged');
    })
  }

  var dragStarted = function(event) {

    elementBeingDragged = event.target;

    while (elementBeingDragged.tagName != 'TR') {
      elementBeingDragged = elementBeingDragged.parentElement
    }

    elementBeingDragged.classList.add('being-dragged')

    // This is required for Firefox. Without it, no dragover events are fired.
    // https://bugzilla.mozilla.org/show_bug.cgi?id=725156
    event.dataTransfer.setData('text/html', null);
  }

  var dropped = function(event) {

    measureTarget = event.target;

    while (measureTarget.tagName != 'TR') {
      measureTarget = measureTarget.parentElement
    }

    if(elementBeingDragged === null || measureTarget.parentElement != elementBeingDragged.parentElement){
      console.log("Can't drag a row to another table");
      measureTarget.classList.remove('drop-destination-above');
      measureTarget.classList.remove('drop-destination-below');
      return
    }

    try {
      if (measureTarget.classList.contains('drop-destination-above')) {
        measureTarget.parentElement.insertBefore(elementBeingDragged, measureTarget);
      } else {
        measureTarget.parentElement.insertBefore(elementBeingDragged, measureTarget.nextSibling);
      }
    } catch(error) {
      console.error(error);
      measureTarget.classList.remove('drop-destination-above');
      measureTarget.classList.remove('drop-destination-below');
      return
    }

    document.querySelectorAll('.drop-destination-above').forEach(function(el) {
       el.classList.remove('drop-destination-above');
    })

    document.querySelectorAll('.drop-destination-below').forEach(function(el) {
       el.classList.remove('drop-destination-below');
    })

    if (this.onDrop) {
      this.onDrop(element)
    }
    event.preventDefault();
  }


  var draggedOver = function(event) {

    if (elementBeingDragged) {

      event.preventDefault()

      var measureTarget = event.target

      while (measureTarget.tagName != 'TR') {
        measureTarget = measureTarget.parentElement
      }

      document.querySelectorAll('.drop-destination-above').forEach(function(el) {
        el.classList.remove('drop-destination-above');
      })

      document.querySelectorAll('.drop-destination-below').forEach(function(el) {
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

  }

  element.addEventListener('dragstart', dragStarted.bind(this));
  element.addEventListener('drop', dropped.bind(this));
  element.addEventListener('dragover', draggedOver.bind(this));
  element.addEventListener('dragend', dragEnded.bind(this));

}