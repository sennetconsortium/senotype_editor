/*
Script that changes the URL behind the "Explore" button for the specified
marker modal, based on the selected organism.
*/
function updateMarkerExploreUrl() {
        const organism = document.querySelector('input[name="marker-organism"]:checked')?.value;
        const exploreButton = document.getElementById('marker-explore');

        if (!exploreButton) return;

        exploreButton.href = organism === 'human' ? '/explore/hgnc' : '/explore/mgi';
    }

    document.querySelectorAll('input[name="marker-organism"]').forEach(radio => {
        radio.addEventListener('change', updateMarkerExploreUrl);
    });

    updateMarkerExploreUrl();