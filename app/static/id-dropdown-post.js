document.addEventListener('DOMContentLoaded', function() {
  const idSelect = document.querySelector('[name="senotypeid"]');
  if (idSelect) {
    idSelect.addEventListener('change', function(e) {
      // Prevent any accidental update form submission
      if (document.activeElement === idSelect) {
        // Disable update button while submitting edit form
        console.log('idselect changed');
        const updateBtn = document.getElementById('update_btn');
        if (updateBtn) updateBtn.disabled = true;
        // Only submit the edit form
        document.getElementById('edit_form').submit();
      }
    });
  }
});