(function() {
  if (!Event.prototype.preventDefault) {
    Event.prototype.preventDefault=function() {
      this.returnValue=false;
    };
  }
  if (!Event.prototype.stopPropagation) {
    Event.prototype.stopPropagation=function() {
      this.cancelBubble=true;
    };
  }
  if (!Element.prototype.addEventListener) {
    var eventListeners=[];

    var addEventListener=function(type,listener /*, useCapture (will be ignored) */) {
      var self=this;
      var wrapper=function(e) {
        e.target=e.srcElement;
        e.currentTarget=self;
        if (typeof listener.handleEvent != 'undefined') {
          listener.handleEvent(e);
        } else {
          listener.call(self,e);
        }
      };
      if (type=="DOMContentLoaded") {
        var wrapper2=function(e) {
          if (document.readyState=="complete") {
            wrapper(e);
          }
        };
        document.attachEvent("onreadystatechange",wrapper2);
        eventListeners.push({object:this,type:type,listener:listener,wrapper:wrapper2});

        if (document.readyState=="complete") {
          var e=new Event();
          e.srcElement=window;
          wrapper2(e);
        }
      } else {
        this.attachEvent("on"+type,wrapper);
        eventListeners.push({object:this,type:type,listener:listener,wrapper:wrapper});
      }
    };
    var removeEventListener=function(type,listener /*, useCapture (will be ignored) */) {
      var counter=0;
      while (counter<eventListeners.length) {
        var eventListener=eventListeners[counter];
        if (eventListener.object==this && eventListener.type==type && eventListener.listener==listener) {
          if (type=="DOMContentLoaded") {
            this.detachEvent("onreadystatechange",eventListener.wrapper);
          } else {
            this.detachEvent("on"+type,eventListener.wrapper);
          }
          eventListeners.splice(counter, 1);
          break;
        }
        ++counter;
      }
    };
    Element.prototype.addEventListener=addEventListener;
    Element.prototype.removeEventListener=removeEventListener;
    if (HTMLDocument) {
      HTMLDocument.prototype.addEventListener=addEventListener;
      HTMLDocument.prototype.removeEventListener=removeEventListener;
    }
    if (Window) {
      Window.prototype.addEventListener=addEventListener;
      Window.prototype.removeEventListener=removeEventListener;
    }
  }
})();
// Function.prototype.bind
//
// A polyfill for Function.prototype.bind. Which lets you bind a defined
// value to the `this` keyword in a function call.
//
// Bind is natively supported in:
//   IE9+
//   Chrome 7+
//   Firefox 4+
//   Safari 5.1.4+
//   iOS 6+
//   Android Browser 4+
//   Chrome for Android 0.16+
//
// Originally from:
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind
if (!Function.prototype.bind) {
  Function.prototype.bind = function (oThis) {
    if (typeof this !== "function") {
      // closest thing possible to the ECMAScript 5
      // internal IsCallable function
      throw new TypeError("Function.prototype.bind - what is trying to be bound is not callable");
    }

    var aArgs = Array.prototype.slice.call(arguments, 1),
        fToBind = this,
        fNOP = function () {},
        fBound = function () {
          return fToBind.apply(this instanceof fNOP && oThis
                 ? this
                 : oThis,
                 aArgs.concat(Array.prototype.slice.call(arguments)));
        };

    fNOP.prototype = this.prototype;
    fBound.prototype = new fNOP();

    return fBound;
  };
}

/*
 * classList.js: Cross-browser full element.classList implementation.
 * 1.1.20170427
 *
 * By Eli Grey, http://eligrey.com
 * License: Dedicated to the public domain.
 *   See https://github.com/eligrey/classList.js/blob/master/LICENSE.md
 */

/*global self, document, DOMException */

/*! @source http://purl.eligrey.com/github/classList.js/blob/master/classList.js */

if ("document" in self) {

// Full polyfill for browsers with no classList support
// Including IE < Edge missing SVGElement.classList
if (!("classList" in document.createElement("_"))
  || document.createElementNS && !("classList" in document.createElementNS("http://www.w3.org/2000/svg","g"))) {

(function (view) {

"use strict";

if (!('Element' in view)) return;

var
    classListProp = "classList"
  , protoProp = "prototype"
  , elemCtrProto = view.Element[protoProp]
  , objCtr = Object
  , strTrim = String[protoProp].trim || function () {
    return this.replace(/^\s+|\s+$/g, "");
  }
  , arrIndexOf = Array[protoProp].indexOf || function (item) {
    var
        i = 0
      , len = this.length
    ;
    for (; i < len; i++) {
      if (i in this && this[i] === item) {
        return i;
      }
    }
    return -1;
  }
  // Vendors: please allow content code to instantiate DOMExceptions
  , DOMEx = function (type, message) {
    this.name = type;
    this.code = DOMException[type];
    this.message = message;
  }
  , checkTokenAndGetIndex = function (classList, token) {
    if (token === "") {
      throw new DOMEx(
          "SYNTAX_ERR"
        , "An invalid or illegal string was specified"
      );
    }
    if (/\s/.test(token)) {
      throw new DOMEx(
          "INVALID_CHARACTER_ERR"
        , "String contains an invalid character"
      );
    }
    return arrIndexOf.call(classList, token);
  }
  , ClassList = function (elem) {
    var
        trimmedClasses = strTrim.call(elem.getAttribute("class") || "")
      , classes = trimmedClasses ? trimmedClasses.split(/\s+/) : []
      , i = 0
      , len = classes.length
    ;
    for (; i < len; i++) {
      this.push(classes[i]);
    }
    this._updateClassName = function () {
      elem.setAttribute("class", this.toString());
    };
  }
  , classListProto = ClassList[protoProp] = []
  , classListGetter = function () {
    return new ClassList(this);
  }
;
// Most DOMException implementations don't allow calling DOMException's toString()
// on non-DOMExceptions. Error's toString() is sufficient here.
DOMEx[protoProp] = Error[protoProp];
classListProto.item = function (i) {
  return this[i] || null;
};
classListProto.contains = function (token) {
  token += "";
  return checkTokenAndGetIndex(this, token) !== -1;
};
classListProto.add = function () {
  var
      tokens = arguments
    , i = 0
    , l = tokens.length
    , token
    , updated = false
  ;
  do {
    token = tokens[i] + "";
    if (checkTokenAndGetIndex(this, token) === -1) {
      this.push(token);
      updated = true;
    }
  }
  while (++i < l);

  if (updated) {
    this._updateClassName();
  }
};
classListProto.remove = function () {
  var
      tokens = arguments
    , i = 0
    , l = tokens.length
    , token
    , updated = false
    , index
  ;
  do {
    token = tokens[i] + "";
    index = checkTokenAndGetIndex(this, token);
    while (index !== -1) {
      this.splice(index, 1);
      updated = true;
      index = checkTokenAndGetIndex(this, token);
    }
  }
  while (++i < l);

  if (updated) {
    this._updateClassName();
  }
};
classListProto.toggle = function (token, force) {
  token += "";

  var
      result = this.contains(token)
    , method = result ?
      force !== true && "remove"
    :
      force !== false && "add"
  ;

  if (method) {
    this[method](token);
  }

  if (force === true || force === false) {
    return force;
  } else {
    return !result;
  }
};
classListProto.toString = function () {
  return this.join(" ");
};

if (objCtr.defineProperty) {
  var classListPropDesc = {
      get: classListGetter
    , enumerable: true
    , configurable: true
  };
  try {
    objCtr.defineProperty(elemCtrProto, classListProp, classListPropDesc);
  } catch (ex) { // IE 8 doesn't support enumerable:true
    // adding undefined to fight this issue https://github.com/eligrey/classList.js/issues/36
    // modernie IE8-MSW7 machine has IE8 8.0.6001.18702 and is affected
    if (ex.number === undefined || ex.number === -0x7FF5EC54) {
      classListPropDesc.enumerable = false;
      objCtr.defineProperty(elemCtrProto, classListProp, classListPropDesc);
    }
  }
} else if (objCtr[protoProp].__defineGetter__) {
  elemCtrProto.__defineGetter__(classListProp, classListGetter);
}

}(self));

}

// There is full or partial native classList support, so just check if we need
// to normalize the add/remove and toggle APIs.

(function () {
  "use strict";

  var testElement = document.createElement("_");

  testElement.classList.add("c1", "c2");

  // Polyfill for IE 10/11 and Firefox <26, where classList.add and
  // classList.remove exist but support only one argument at a time.
  if (!testElement.classList.contains("c2")) {
    var createMethod = function(method) {
      var original = DOMTokenList.prototype[method];

      DOMTokenList.prototype[method] = function(token) {
        var i, len = arguments.length;

        for (i = 0; i < len; i++) {
          token = arguments[i];
          original.call(this, token);
        }
      };
    };
    createMethod('add');
    createMethod('remove');
  }

  testElement.classList.toggle("c3", false);

  // Polyfill for IE 10 and Firefox <24, where classList.toggle does not
  // support the second argument.
  if (testElement.classList.contains("c3")) {
    var _toggle = DOMTokenList.prototype.toggle;

    DOMTokenList.prototype.toggle = function(token, force) {
      if (1 in arguments && !this.contains(token) === !force) {
        return force;
      } else {
        return _toggle.call(this, token);
      }
    };

  }

  testElement = null;
}());

}
if (Object.defineProperty
  && Object.getOwnPropertyDescriptor
  && Object.getOwnPropertyDescriptor(Element.prototype, "textContent")
  && !Object.getOwnPropertyDescriptor(Element.prototype, "textContent").get) {
  (function() {
    var innerText = Object.getOwnPropertyDescriptor(Element.prototype, "innerText");
    Object.defineProperty(Element.prototype, "textContent",
     {
       get: function() {
         return innerText.get.call(this);
       },
       set: function(s) {
         return innerText.set.call(this, s);
       }
     }
   );
  })();
}

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


function Accordion(element) {

  // First do feature detection for required API methods
  if (
    document.querySelectorAll &&
    window.NodeList &&
    'classList' in document.body
  ) {

    this.element = element
    this.sections = []
    this.setup()

  }

}

function AccordionSection(element, accordion) {
  this.element = element
  this.accordion = accordion
  this.setup()
}

Accordion.prototype.setup = function() {

  var accordion_sections = this.element.querySelectorAll('.accordion-section')

  var accordion = this

  for (var i = accordion_sections.length - 1; i >= 0; i--) {
     accordion.sections.push(new AccordionSection(accordion_sections[i], accordion))
  };

  var accordion_controls = document.createElement('div')
  accordion_controls.setAttribute('class', 'accordion-controls')

  var open_or_close_all_button = document.createElement('button')
  open_or_close_all_button.textContent = 'Open all'
  open_or_close_all_button.setAttribute('class', 'accordion-expand-all')
  open_or_close_all_button.setAttribute('aria-expanded', 'false')

  open_or_close_all_button.addEventListener('click', this.openOrCloseAll.bind(this))

  accordion_controls.appendChild(open_or_close_all_button)

  this.element.insertBefore(accordion_controls, this.element.firstChild)
  this.element.classList.add('with-js')
}

Accordion.prototype.openOrCloseAll = function(event) {

  var open_or_close_all_button = event.target
  var now_expanded = !(open_or_close_all_button.getAttribute('aria-expanded') == 'true')

  for (var i = this.sections.length - 1; i >= 0; i--) {
    this.sections[i].setExpanded(now_expanded)
  };

  this.setOpenCloseButtonExpanded(now_expanded)

}


Accordion.prototype.setOpenCloseButtonExpanded = function(expanded) {

  var open_or_close_all_button = this.element.querySelector('.accordion-expand-all')

  var new_button_text = expanded ? "Close all" : "Open all"
  open_or_close_all_button.setAttribute('aria-expanded', expanded)
  open_or_close_all_button.textContent = new_button_text

}

Accordion.prototype.updateOpenAll = function() {

  var sectionsCount = this.sections.length

  var openSectionsCount = 0

  for (var i = this.sections.length - 1; i >= 0; i--) {
    if (this.sections[i].expanded()) {
      openSectionsCount += 1
    }
  };

  if (sectionsCount == openSectionsCount) {
    this.setOpenCloseButtonExpanded(true)
  } else {
    this.setOpenCloseButtonExpanded(false)
  }

}

AccordionSection.prototype.setup = function() {
  this.element.setAttribute('aria-expanded', 'false')

  var header = this.element.querySelector('.accordion-section-header')
  header.addEventListener('click', this.toggleExpanded.bind(this))

  var icon = document.createElement('span')
  icon.setAttribute('class', 'icon')

  header.appendChild(icon)
}

AccordionSection.prototype.toggleExpanded = function(){
  var expanded = (this.element.getAttribute('aria-expanded') == 'true')

  this.setExpanded(!expanded)
  this.accordion.updateOpenAll()
}

AccordionSection.prototype.expanded = function() {
  return (this.element.getAttribute('aria-expanded') == 'true')
}

AccordionSection.prototype.setExpanded = function(expanded) {
  this.element.setAttribute('aria-expanded', expanded)

  // This is set to trigger reflow for IE8, which doesn't
  // always reflow after a setAttribute call.
  this.element.className = this.element.className

}

if (
  'addEventListener' in document &&
  document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {

    var accordions = document.querySelectorAll('.accordion')

    for (var i = accordions.length - 1; i >= 0; i--) {
      new Accordion(accordions[i])
    };

  })

}

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

  var inputFields = this.fieldset.querySelectorAll('input')

  var anyFieldsHaveValue = false;

  for (var i = inputFields.length - 1; i >= 0; i--) {

    if (inputFields[i].value != "") {
      anyFieldsHaveValue = true
      break;
    }
  };

  if (!anyFieldsHaveValue) {

    this.fieldset.classList.add('hidden')

    this.add_second_contact_button = document.createElement('button')
    this.add_second_contact_button.classList.add('link')
    this.add_second_contact_button.textContent = 'Add second contact'
    this.add_second_contact_button.addEventListener('click', this.expandFieldset.bind(this))

    var parent = this.fieldset.parentElement

    parent.insertBefore(this.add_second_contact_button, this.fieldset)

  }

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

    var fields = that.fieldset.querySelectorAll('input, textarea')
    var anyFieldsHaveValue = false;

    for (var i = fields.length - 1; i >= 0; i--) {

      if (fields[i].value != "") {
        anyFieldsHaveValue = true
        break;
      }
    };

    that.add_secondary_source_button = document.createElement('button')
    that.add_secondary_source_button.classList.add('link')
    that.add_secondary_source_button.classList.add('hidden')
    that.add_secondary_source_button.textContent = 'Add secondary source'
    that.add_secondary_source_button.addEventListener('click', that.addSourceButtonClicked.bind(that))
    var parent = that.fieldset.parentElement
    parent.insertBefore(that.add_secondary_source_button, that.fieldset)


    var remove_secondary_source_button = document.createElement('button')
    remove_secondary_source_button.classList.add('delete')
    remove_secondary_source_button.classList.add('link')
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



SecondarySources.prototype.showButtonForFirstHiddenSource = function() {

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


SecondarySource.prototype.setHidden = function(hidden) {
  this.hidden = hidden

  if (hidden) {
    this.fieldset.classList.add('hidden')
  } else {
    this.fieldset.classList.remove('hidden')
  }

  this.secondary_sources.showButtonForFirstHiddenSource()
}

SecondarySource.prototype.showAddSourceButton = function(show) {

  if (show) {
    this.add_secondary_source_button.classList.remove('hidden')
  } else {
    this.add_secondary_source_button.classList.add('hidden')
  }

}


SecondarySource.prototype.addSourceButtonClicked = function(event) {

  this.setHidden(false)
  event.preventDefault()
};

SecondarySource.prototype.removeSourceButtonClicked = function(event) {

  var fields = this.fieldset.querySelectorAll('input, textarea')

  for (var i = 0; i < fields.length; i++) {
    fields[i].value = ""
  };

  this.setHidden(true)
  event.preventDefault()
};

if (
  'addEventListener' in document &&
  document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {
    var secondary_sources = document.querySelectorAll('.js-secondary-sources')

    for (var i = secondary_sources.length - 1; i >= 0; i--) {
      new SecondarySources(secondary_sources[i])
    };

  })

}
function SortableTable(table, header_table, options) {

  // First do feature detection for required API methods
  if (
    document.querySelectorAll &&
    document.querySelector &&
    window.NodeList
    ) {

      this.table = table;
      this.header_table = header_table;
      this.setupOptions(options);
      this.createHeadingButtons();
      this.createStatusBox();

    }
};

SortableTable.prototype.setupOptions = function(options) {
    options = options || {};
    options.statusMessage = options.statusMessage || 'Sort by %heading% (%direction%)';
    options.ascendingText = options.ascendingText || 'ascending';
    options.descendingText = options.descendingText || 'descending';
    this.options = options;
};

SortableTable.prototype.createHeadingButtons = function() {

  var header_rows = this.table.querySelectorAll('thead tr')

  for (var j = 0; j < header_rows.length; j++) {

    var headings = header_rows[j].querySelectorAll('th')
    var heading;

    for(var i = 0; i < headings.length; i++) {
        heading = headings[i];
        if(heading.getAttribute('aria-sort')) {
            this.createHeadingButton(heading, i);
        }
    }

  };

  if (this.header_table) {

    var header_rows = this.header_table.querySelectorAll('thead tr')

    for (var j = 0; j < header_rows.length; j++) {


      var headings = header_rows[j].querySelectorAll('th')
      var heading;

      for(var i = 0; i < headings.length; i++) {
          heading = headings[i];
          if(heading.getAttribute('aria-sort')) {
              this.createHeadingButton(heading, i);
          }
      }


    };


  }
};

SortableTable.prototype.createHeadingButton = function(heading, i) {
    var text = heading.textContent;
    var button = document.createElement('button')
    button.setAttribute('type', 'button')
    button.setAttribute('data-index', i)
    button.textContent = text
    button.addEventListener('click', this.sortButtonClicked.bind(this))
    heading.textContent = '';
    heading.appendChild(button);
};

SortableTable.prototype.createStatusBox = function() {

    this.status = document.createElement('div')
    this.status.setAttribute('aria-live', 'polite')
    this.status.setAttribute('role', 'status')
    this.status.setAttribute('aria-atomic', 'true')
    this.status.setAttribute('class', 'sortableTable-status visuallyhidden')

    this.table.parentElement.appendChild(this.status);
};

SortableTable.prototype.sortButtonClicked = function(event) {

  var columnNumber = event.target.getAttribute('data-index')
  var sortDirection = event.target.parentElement.getAttribute('aria-sort')
  var newSortDirection;
    if(sortDirection === 'none' || sortDirection === 'ascending') {
        newSortDirection = 'descending';
    } else {
        newSortDirection = 'ascending';
    }

  var tBodies = this.table.querySelectorAll('tbody')

  this.sortTBodies(tBodies,columnNumber,newSortDirection)

  for (var i = tBodies.length - 1; i >= 0; i--) {

    var rows = this.getTableRowsArray(tBodies[i])
    var sortedRows = this.sort(rows, columnNumber, newSortDirection);
    this.addRows(tBodies[i], sortedRows);

  };

  this.removeButtonStates();
  this.updateButtonState(event.target, newSortDirection);

}

SortableTable.prototype.sortTBodies = function(tBodies, columnNumber, sortDirection) {

  var tBodiesAsArray = []
  var _this = this

  for (var i = 0; i < tBodies.length; i++) {
    tBodiesAsArray.push(tBodies[i])
  };

  var newTbodies = tBodiesAsArray.sort(function(tBodyA, tBodyB) {

    var tBodyAHeaderRow = tBodyA.querySelector('th[scope="rowgroup"]')

    var tBodyBHeaderRow = tBodyB.querySelector('th[scope="rowgroup"]')


    if (tBodyAHeaderRow && tBodyBHeaderRow) {
      tBodyAHeaderRow = tBodyAHeaderRow.parentElement
      tBodyBHeaderRow = tBodyBHeaderRow.parentElement

      var tBodyACell = tBodyAHeaderRow.querySelectorAll('td, th')[columnNumber]
      var tBodyBCell = tBodyBHeaderRow.querySelectorAll('td, th')[columnNumber]

      var tBodyAValue = _this.getCellValue(tBodyACell)
      var tBodyBValue = _this.getCellValue(tBodyBCell)

      return _this.compareValues(tBodyAValue, tBodyBValue, sortDirection)

    } else {

      console.log('no way to compare tbodies')
      return 0
    }


  });

  for (var i = 0; i < newTbodies.length; i++) {
    this.table.appendChild(newTbodies[i])
  };

}

SortableTable.prototype.compareValues = function(valueA, valueB, sortDirection) {

  if(sortDirection === 'ascending') {
      if(valueA < valueB) {
          return -1;
      }
      if(valueA > valueB) {
          return 1;
      }
      return 0;
  } else {
      if(valueB < valueA) {
          return -1;
      }
      if(valueB > valueA) {
          return 1;
      }
      return 0;
  }

}

SortableTable.prototype.updateButtonState = function(button, direction) {
    button.parentElement.setAttribute('aria-sort', direction);
    var message = this.options.statusMessage;
    message = message.replace(/%heading%/, button.textContent);
    message = message.replace(/%direction%/, this.options[direction+'Text']);
    this.status.textContent = message;
};

SortableTable.prototype.removeButtonStates = function() {

    var tableHeaders = this.table.querySelectorAll('thead th')

    for (var i = tableHeaders.length - 1; i >= 0; i--) {
      tableHeaders[i].setAttribute('aria-sort', 'none')
    };

    if (this.header_table) {

      var tableHeaders = this.header_table.querySelectorAll('thead th')

      for (var i = tableHeaders.length - 1; i >= 0; i--) {
        tableHeaders[i].setAttribute('aria-sort', 'none')
      };

    }

};

SortableTable.prototype.addRows = function(tbody, rows) {
    for(var i = 0; i < rows.length; i++) {
        tbody.appendChild(rows[i]);
    }
};

SortableTable.prototype.getTableRowsArray = function(tbody) {
    var rows = [];
    var trs = tbody.querySelectorAll('tr');
    for (var i = 0; i < trs.length; i++) {
        rows.push(trs[i]);
    }
    return rows;
};

SortableTable.prototype.sort = function(rows, columnNumber, sortDirection) {


    var _this = this

    var newRows = rows.sort(function(rowA, rowB) {

      var tdA = rowA.querySelectorAll('td, th')[columnNumber]
      var tdB = rowB.querySelectorAll('td, th')[columnNumber]

      var rowAIsHeader = rowA.querySelector('th[scope="rowgroup"]')
      var rowBIsHeader = rowB.querySelector('th[scope="rowgroup"]')

      var valueA = _this.getCellValue(tdA)
      var valueB = _this.getCellValue(tdB)

        if (rowAIsHeader) {
          return -1
        } else if (rowBIsHeader) {
          return 1
        } else {

          if(sortDirection === 'ascending') {
              if(valueA < valueB) {
                  return -1;
              }
              if(valueA > valueB) {
                  return 1;
              }
              return 0;
          } else {
              if(valueB < valueA) {
                  return -1;
              }
              if(valueB > valueA) {
                  return 1;
              }
              return 0;
          }

        }

    });
    return newRows

};

SortableTable.prototype.getCellValue = function(cell) {

  var cellValue

  if (cell) {

    if (cell.children.length == 1 && cell.children[0].tagName == "TIME") {

      var timeElement = cell.children[0]

      if (timeElement.getAttribute('datetime')) {
        cellValue = Date.parse(timeElement.getAttribute('datetime'))
      } else {
        cellValue = Date.parse(timeElement.textContent)
      }

    } else {

      cellValue = cell.getAttribute('data-sort-value') || cell.textContent

      /* Remove commas */
      cellValue = cellValue.replace(/[,]/gi, '')

      cellValue = parseFloat(cellValue) || cellValue

    }

  }

  return cellValue
}
function TableWithFixedHeader(tableElement) {
  var tableElement = tableElement
  var fixedTable, parentParentElement, tableHeader, fixedTableContainer

  function setup() {

    if (tableElement) {
      var parentElement = tableElement.parentElement

      if (parentElement) {
        parentParentElement = parentElement.parentElement

        tableHeader = tableElement.querySelector('thead')

        var fixedTableHeader = tableHeader.cloneNode(true)
        fixedTableHeader.classList.add('fixed')

        fixedTable = document.createElement('table')
        fixedTable.setAttribute('class', tableElement.getAttribute('class') + ' fixed')
        fixedTable.classList.remove('fixed-headers')

        fixedTable.appendChild(fixedTableHeader)

        fixedTableContainer = document.createElement('div')
        fixedTableContainer.classList.add('fixed-header-container')

        fixedTableContainer.appendChild(fixedTable)

        parentParentElement.appendChild(fixedTableContainer)

        // updatePositioning()

        /* Update again after 200ms. Solves a few weird issues. */
        setTimeout(updatePositioning, 200)

        window.addEventListener('resize', updatePositioning)
      }
    }
  }

  function updatePositioning() {

    var height = heightForElement(tableHeader);

    tableElement.style.marginTop = '-' + height;
    parentParentElement.style.paddingTop = height;

    var mainTableHeaderCells = tableElement.querySelectorAll('thead th, thead td')
    var headerCells = fixedTable.querySelectorAll('thead th, thead td')

    for (var i = 0; i < mainTableHeaderCells.length; i++) {
      headerCells[i].style.width = widthForElement(mainTableHeaderCells[i])
    };



    fixedTableContainer.style.width = '100000px' // Temporarily set to be super-wide

    var innerContainerWidth = widthForElement(parentParentElement);
    var fixedTableHeaderWidth = widthForElement(fixedTable)

    parentParentElement.style.width = widthForElement(fixedTable);  // Calculate width of table
    fixedTableContainer.style.width = widthForElement(fixedTable);  // Reset to actual width




  }

  function heightForElement(element) {

    if (typeof window.getComputedStyle === "function") {
      return getComputedStyle(element).height
    } else {
      return element.getBoundingClientRect().bottom - element.getBoundingClientRect().top;
    }


  }

  function widthForElement(element) {

    if (typeof window.getComputedStyle === "function") {
      return getComputedStyle(element).width
    } else {
      return element.getBoundingClientRect().right - element.getBoundingClientRect().left;
    }

  }

  // Check for required APIs
  if (
    document.querySelector &&
    document.body.classList
  ) {
    setup()
  }


}
// = require_tree ./govuk


$(document).ready(function () {
  var $details = $('details');
  $details.each(function () {
    $(this).after('<div class="print-node"><h3 class="heading-small">' + $(this).find('span').html() + '</h3><div>' + $(this).find('.panel').html() + '</div></div>')
  });

  $('.js--print').click(function (e) {
    e.preventDefault();
    window.print();
  });
});
// Stageprompt 2.0.1
//
// See: https://github.com/alphagov/stageprompt
//
// Stageprompt allows user journeys to be described and instrumented
// using data attributes.
//
// Setup (run this on document ready):
//
//   GOVUK.performance.stageprompt.setupForGoogleAnalytics();
//
// Usage:
//
//   Sending events on page load:
//
//     <div id="wrapper" class="service" data-journey="pay-register-birth-abroad:start">
//         [...]
//     </div>
//
//   Sending events on click:
//
//     <a class="help-button" href="#" data-journey-click="stage:help:info">See more info...</a>

;(function (global) {
  'use strict'

  var $ = global.jQuery
  var GOVUK = global.GOVUK || {}

  GOVUK.performance = GOVUK.performance || {}

  GOVUK.performance.stageprompt = (function () {
    var setup, setupForGoogleAnalytics, splitAction

    splitAction = function (action) {
      var parts = action.split(':')
      if (parts.length <= 3) return parts
      return [parts.shift(), parts.shift(), parts.join(':')]
    }

    setup = function (analyticsCallback) {
      var journeyStage = $('[data-journey]').attr('data-journey')
      var journeyHelpers = $('[data-journey-click]')

      if (journeyStage) {
        analyticsCallback.apply(null, splitAction(journeyStage))
      }

      journeyHelpers.on('click', function (event) {
        analyticsCallback.apply(null, splitAction($(this).data('journey-click')))
      })
    }

    setupForGoogleAnalytics = function () {
      setup(GOVUK.performance.sendGoogleAnalyticsEvent)
    }

    return {
      setup: setup,
      setupForGoogleAnalytics: setupForGoogleAnalytics
    }
  }())

  GOVUK.performance.sendGoogleAnalyticsEvent = function (category, event, label) {
    global._gaq.push(['_trackEvent', category, event, label, undefined, true])
  }

  global.GOVUK = GOVUK
})(window)

$(document).ready(function () {
  var $stickies = $(".sticky-js");
  $.each($stickies, function () {
    var stickyPosition = parseInt($(this).position().top);
    $(window).scroll(function () {
      var scrollTop = $(window).scrollTop();
      if (scrollTop >= stickyPosition) {
        $(this).addClass('sticky-js-fixed');
      } else {
        $(this).removeClass('sticky-js-fixed');
      }
    }.bind(this));
  });
});

if ('addEventListener' in document &&
    document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {

    var fixedTableContainers = document.querySelectorAll('.table-container-outer.fixed-headers')

    for (var i = 0; i < fixedTableContainers.length; i++) {

      var table = fixedTableContainers[i].querySelector('table')
      new TableWithFixedHeader(table)

    };

  })

}

if ('addEventListener' in document &&
    document.querySelectorAll
  ) {

  document.addEventListener('DOMContentLoaded', function() {

    var tables = document.querySelectorAll('.table-container-outer')

    for (var i = tables.length - 1; i >= 0; i--) {

      var table = tables[i].querySelector('table')
      var header_table = tables[i].querySelector('table.fixed')

      new SortableTable(table, header_table, {})
    };

  })

}