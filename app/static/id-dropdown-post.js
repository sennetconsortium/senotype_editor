// Changing the ID list in the edit form triggers a post to the form so that the
// form can populate from existing data.
document.addEventListener('DOMContentLoaded', function() {
  const idSelect = document.querySelector('[name="senotypeid"]');
  if (idSelect) {
    idSelect.addEventListener('change', function() {
      document.getElementById('edit_form').submit();
    });
  }
});