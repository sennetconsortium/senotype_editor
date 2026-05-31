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

function updateregMarkerExploreUrl() {
        const organism = document.querySelector('input[name="regmarker-organism"]:checked')?.value;
        const exploreButton = document.getElementById('regmarker-explore');

        if (!exploreButton) return;

        exploreButton.href = organism === 'human' ? '/explore/hgnc' : '/explore/mgi';
    }

    document.querySelectorAll('input[name="regmarker-organism"]').forEach(radio => {
        radio.addEventListener('change', updateregMarkerExploreUrl);
    });

    updateregMarkerExploreUrl();