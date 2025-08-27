// Only submit the edit_form if the user actually changes the Senotype ID value.
// This prevents accidental submission if the select is focused and a modal button is clicked.

document.addEventListener('DOMContentLoaded', function() {
  const idSelect = document.querySelector('[name="senotypeid"]');
  let lastValue = idSelect ? idSelect.value : null;
  if (idSelect) {
    idSelect.addEventListener('change', function(e) {
      // Only submit if the value actually changed
      if (idSelect.value !== lastValue) {
        lastValue = idSelect.value;
        // Optionally disable the update button while submitting
        const updateBtn = document.getElementById('update_btn');
        if (updateBtn) updateBtn.disabled = true;
        document.getElementById('edit_form').submit();
      }
    });
  }
});