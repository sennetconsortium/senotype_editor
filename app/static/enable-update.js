// Enable the update button only if there is a change in input.

document.addEventListener('DOMContentLoaded', function() {
  const editForm = document.getElementById('edit_form');
  const updateBtn = document.getElementById('update_btn');

  // Store initial form data as serialized string
  let initialData = new FormData(editForm);
  let initialSerialized = serializeFormData(initialData);

  // Listen for any input, change, or textarea event in the edit form
  editForm.addEventListener('input', checkForChange);
  editForm.addEventListener('change', checkForChange);

  function checkForChange() {
    const currentData = new FormData(editForm);
    const currentSerialized = serializeFormData(currentData);
    updateBtn.disabled = (currentSerialized === initialSerialized);
  }

  // Helper function to serialize FormData for comparison
  function serializeFormData(formData) {
    // FormData is not directly comparable, so we convert it to a sorted query string
    return Array.from(formData.entries())
      .map(([key, value]) => encodeURIComponent(key) + '=' + encodeURIComponent(value))
      .sort()
      .join('&');
  }
});