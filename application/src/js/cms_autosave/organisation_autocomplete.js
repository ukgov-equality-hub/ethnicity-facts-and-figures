// Function from original CMS form page for type-ahead select

document.addEventListener('DOMContentLoaded', function () {
  var publisherFields = document.querySelectorAll('select.publisher')
  for (var i = 0; i < publisherFields.length; i++) {
    govukGovernmentOrganisationsAutocomplete({
      selectElement: publisherFields[i],
      showAllValues: false,
      minLength: 2,
      defaultValue: ''
    })
  }
})
