const roadmap = document.querySelector('.roadmap-page');

function targetFor(hash) {
    try {
        const target = document.getElementById(decodeURIComponent(hash.slice(1)));
        return roadmap.contains(target) ? target : null;
    } catch (error) {
        if (error instanceof URIError) return null;
        throw error;
    }
}

function reveal(target) {
    const entry = target.closest('[data-roadmap-entry]');
    const isEntryAnchor = target === entry || target.matches('.roadmap-anchor');
    let disclosure = isEntryAnchor ? entry?.querySelector(':scope > details') : target.closest('details');
    while (disclosure) {
        disclosure.open = true;
        disclosure = disclosure.parentElement.closest('details');
    }
}

function revealLocation() {
    const target = targetFor(window.location.hash);
    if (!target) return;
    reveal(target);
    // Let the disclosures enter layout before scrolling to the fragment.
    requestAnimationFrame(() => {
        if (targetFor(window.location.hash) === target) target.scrollIntoView({ behavior: 'instant' });
    });
}

roadmap.addEventListener('click', (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    const target = targetFor(link.hash);
    if (!target) return;
    if (link.hash === window.location.hash) revealLocation();
    else reveal(target);
});

window.addEventListener('hashchange', revealLocation);
window.addEventListener('pageshow', (event) => {
    if (!event.persisted) revealLocation();
});
