/**
 * Dynamically adds link buttons next to hidden input elements, before the remove button.
 * @param {string} url_base - The base URL to use for the anchor's href (will append the hidden input's value).
 * @param {string} hidden_input_selector - A CSS selector for the hidden input(s) whose value will be used.
 * @param {string} link_title - The title attribute for the anchor.
 * @param {string} target_selector - Selector for the placeholder (e.g. '.dataset-link-placeholder').
 */
function addLinkButtons(url_base, hidden_input_selector, link_title, target_selector) {
    document.querySelectorAll(hidden_input_selector).forEach(function(hiddenInput) {
        var hiddenValue = hiddenInput.value;

        // Find the container <li>
        var containerLi = hiddenInput.closest('li');
        if (!containerLi) return;

        // Find the remove button in this <li>
        var removeBtn = containerLi.querySelector('button.btn-danger');
        // Find the placeholder span in this <li>
        var placeholder = containerLi.querySelector(target_selector);

        if (placeholder) {
            var link = document.createElement('a');
            link.className = 'btn btn-sm btn-outline-primary ms-2';
            link.style.width = '2.5em';
            link.href = url_base + encodeURIComponent(hiddenValue);
            link.target = '_blank';
            link.title = link_title;
            link.textContent = '🔗';

            // Insert the link before the remove button
            if (removeBtn) {
                containerLi.insertBefore(link, removeBtn);
            } else {
                placeholder.appendChild(link);
            }
        }
    });
}