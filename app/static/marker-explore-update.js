// Update the link for the explore button for any radio group named "*-type".


// Used to update links in the selection modals for specified and regulating makers:

//   radio name="marker-type"   -> link id "marker-explore" or "marker_explore"
//   radio name="regmarker-type" -> link id "regmarker-explore" or "regmarker_explore"

document.addEventListener('DOMContentLoaded', function () {
  // Find all radio inputs whose name ends with "-type"
  const radios = Array.from(document.querySelectorAll('input[name$="-type"]'));
  if (!radios.length) return;

  // Get unique radio group names
  const groupNames = Array.from(new Set(radios.map(r => r.name)));

  // Mapping for common values -> explore path
  const valueToPath = {
    'gene': '/explore/hgnc',
    'protein': '/explore/uniprotkb'
  };

  groupNames.forEach(function(groupName) {
    // Candidate link IDs derived from the group name:
    // replace "-type" with "-explore" (hyphen) or "_explore" (underscore)
    const base = groupName.replace(/-type$/, '');
    const idCandidates = [base + '-explore', base + '_explore'];

    // Find the first existing explore link for this group
    let exploreLink = null;
    for (const id of idCandidates) {
      exploreLink = document.getElementById(id);
      if (exploreLink) break;
    }
    if (!exploreLink) {
      // Nothing to update for this group
      return;
    }

    function updateForGroup() {
      const selected = document.querySelector(`input[name="${groupName}"]:checked`);
      if (!selected) return;
      const value = selected.value;

      // If the link element defines explicit targets via data attributes, prefer them:
      // data-explore-gene, data-explore-protein, or data-explore-default
      let href = null;
      if (value === 'gene' && exploreLink.dataset.exploreGene) {
        href = exploreLink.dataset.exploreGene;
      } else if (value === 'protein' && exploreLink.dataset.exploreProtein) {
        href = exploreLink.dataset.exploreProtein;
      } else if (exploreLink.dataset.exploreDefault) {
        href = exploreLink.dataset.exploreDefault.replace('{value}', encodeURIComponent(value));
      } else {
        // Fallback to HGNC
        href = valueToPath[value] || ('/explore/hgnc');
      }

      exploreLink.setAttribute('href', href);
      exploreLink.setAttribute('aria-label', `Explore (${value})`);
      exploreLink.title = `Explore ${value}`;
    }

    // Attach listeners to all radios in the group
    const groupInputs = Array.from(document.querySelectorAll(`input[name="${groupName}"]`));
    groupInputs.forEach(function(r) {
      r.addEventListener('change', updateForGroup);
    });

    // Initialize once on load
    updateForGroup();
  });
});