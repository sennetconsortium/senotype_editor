/*
 Dynamically adds link buttons next to hidden input elements, before the remove button.
 * @param {string} url_base - The base URL to use for the anchor's href (will append the hidden input's value or parsed code).
 * @param {string} hidden_input_selector - A CSS selector for the hidden input(s) whose value will be used.
 * @param {string} link_title - The title attribute for the anchor.
 * @param {string} target_selector - Selector for the placeholder (e.g. '.dataset-link-placeholder').
 * @param {boolean} parse_code - If true, use the part of the hidden input's value after the ':' character.
 */
function addLinkButtons(url_base, hidden_input_selector, link_title, target_selector, parse_code) {
    document.querySelectorAll(hidden_input_selector).forEach(function(hiddenInput) {
        var hiddenValue = hiddenInput.value;
        var code = hiddenValue;

        if (parse_code && hiddenValue.includes(':')) {
            code = hiddenValue.split(':')[1];
        }

        // For textarea, parent container is not <li>
        var parent = hiddenInput.closest('.d-flex') || hiddenInput.parentElement;
        if (!parent) return;

        var placeholder = parent.querySelector(target_selector);
        if (placeholder) {
            var link = document.createElement('a');
            link.className = 'btn btn-sm btn-outline-primary ms-2';
            link.style.width = '2.5em';
            link.href = url_base + encodeURIComponent(code);
            link.target = '_blank';
            link.title = link_title;
            link.setAttribute('aria-label', link_title);
            link.textContent = '🔗';
            placeholder.innerHTML = '';
            placeholder.appendChild(link);
        }
    });
}