function DynamicResizingTextarea(element) {
  this.element = element
}

DynamicResizingTextarea.prototype.init = function() {
  // feature-detect required APIs
  if ('addEventListener' in document &&
      'scrollHeight' in document.body &&
      'classList' in document.body &&
      Function.prototype.bind) {

    this.element.classList.add('js-autoresize')
    this.element.rows = "1";
    this.updateHeight()
    this.element.addEventListener('input', this.updateHeight.bind(this))

  }
}

DynamicResizingTextarea.prototype.updateHeight = function() {
  this.element.style.height = 'auto'; // Need to do this in order to properly calculate `this.scrollHeight`
  this.element.style.height = (this.element.scrollHeight) + 'px';
}


// Automatically add this to any elements with the data-module attribute
if ('addEventListener' in document) {
  document.addEventListener('DOMContentLoaded', function () {
    var autoResizeElements = document.querySelectorAll('[data-module~="autoresize"]')
    for (var i = 0; i < autoResizeElements.length; i++) {
      new DynamicResizingTextarea(autoResizeElements[i]).init()
    }
  });
}
