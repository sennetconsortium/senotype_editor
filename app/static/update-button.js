document.addEventListener("DOMContentLoaded", function () {
    const editForm = document.getElementById("edit_form");
    const updateForm = document.getElementById("update_form");
    const updateBtn = document.getElementById("update_btn");

    // List of list element IDs to track for changes (these are in edit_form, not modals)
    const listIds = [
        "taxon-list", "location-list", "celltype-list", "hallmark-list", "observable-list", "inducer-list",
        "assay-list", "citation-list", "origin-list", "dataset-list", "marker-list", "regmarker-list"
    ];

    // Helper to get current form state (excluding modal fields/divs)
    function getFormState() {
        const elements = Array.from(editForm.elements).filter(el =>
            (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA")
            && el.type !== "hidden"
            && editForm.contains(el)
        );
        const inputState = elements.map(el =>
            el.type === "checkbox" || el.type === "radio"
                ? el.checked
                : el.value
        );
        // Add list state as stringified HTML, but only for lists inside editForm
        const listState = listIds.map(id => {
            const ul = document.getElementById(id);
            if (ul && editForm.contains(ul)) {
                return ul.innerHTML;
            } else {
                return "";
            }
        });
        return inputState.concat(listState);
    }

    // Store initial state
    const initialState = getFormState();

    function checkChanged() {
        const currentState = getFormState();
        const changed = currentState.some((val, i) => val !== initialState[i]);
        updateBtn.disabled = !changed;
    }

    // Listen for input/change events for fields
    editForm.addEventListener("input", checkChanged);
    editForm.addEventListener("change", checkChanged);

    // Listen for changes to the lists (add/remove)
    listIds.forEach(id => {
        const ul = document.getElementById(id);
        if (ul && editForm.contains(ul)) {
            const observer = new MutationObserver(checkChanged);
            observer.observe(ul, { childList: true, subtree: false });
        }
    });

    // On update_form submit, copy non-modal edit_form inputs to update_form
    updateForm.addEventListener("submit", function (e) {
        // Remove previously added hidden inputs
        Array.from(updateForm.querySelectorAll(".cloned-edit-input")).forEach(el => el.remove());

        // Get all inputs/selects/textareas in edit_form (excluding modal forms)
        // Only consider elements that are actually in editForm (not modals)
        const elements = Array.from(editForm.elements).filter(el =>
            (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA")
            && el.type !== "hidden"
            && editForm.contains(el)
        );
        elements.forEach(el => {
            let value;
            if (el.type === "checkbox" || el.type === "radio") {
                if (!el.checked) return; // skip unchecked
                value = el.value;
            } else {
                value = el.value;
            }
            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = el.name;
            hidden.value = value;
            hidden.className = "cloned-edit-input";
            updateForm.appendChild(hidden);
        });

        // For lists: copy values of inputs inside lists
        listIds.forEach(id => {
            const ul = document.getElementById(id);
            if (ul && editForm.contains(ul)) {
                Array.from(ul.querySelectorAll("input,select,textarea")).forEach(el => {
                    if (!el.name) return;
                    const hidden = document.createElement("input");
                    hidden.type = "hidden";
                    hidden.name = el.name;
                    hidden.value = el.value;
                    hidden.className = "cloned-edit-input";
                    updateForm.appendChild(hidden);
                });
            }
        });
        // Submit proceeds
    });
});