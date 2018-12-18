function NoNewlinesTextarea (element) {
  this.element = element
}

NoNewlinesTextarea.prototype.init = function () {
  if ('addEventListener' in document &&
      Function.prototype.bind) {
    this.element.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault()
      }
    })
    this.element.addEventListener('input', this.stripNewlines.bind(this))
    this.stripNewlines()
  }
}

NoNewlinesTextarea.prototype.stripNewlines = function () {
  if (this.element.value.indexOf('\r') !== -1 || this.element.value.indexOf('\n') !== -1) {
    this.element.value = this.element.value.replace(/[\r\n]/gm, '')
  }
}

if ('addEventListener' in document) {
  document.addEventListener('DOMContentLoaded', function () {
    var noNewlineElements = document.querySelectorAll('[data-module~="no-newlines"]')
    for (var i = 0; i < noNewlineElements.length; i++) {
      new NoNewlinesTextarea(noNewlineElements[i]).init()
    }
  })
}
