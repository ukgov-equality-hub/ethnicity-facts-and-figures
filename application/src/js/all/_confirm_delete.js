
function showDeleteForm(measure) {
    document.getElementById('measure-action-section-' + measure).style.display = 'none';
    document.getElementById('measure-action-section__delete-' + measure).style.display = 'block';
    return false;
}

function submitDeleteForm(measure) {
    var yesBtn = document.getElementById('delete-radio-yes-' + measure);
    var noBtn = document.getElementById('delete-radio-no-' + measure);
    if(yesBtn.checked === true) {
        return true;
    } else {
        return hideDeleteForm(measure);
    }
}

function hideDeleteForm(measure) {
    document.getElementById('measure-action-section__delete-' + measure).style.display = 'none';
    document.getElementById('measure-action-section-' + measure).style.display = 'block';
    return false;
}
