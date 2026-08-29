/**
 * Template Loader for the Tournament component.
 *
 * The tournament UI template is split across several .html fragment files so the
 * markup is easier to read and edit than a single ~100KB JS file. This module
 * loads those fragments (synchronously, via XHR, because Vue needs the template
 * string at component-definition time) and inlines them into one template string.
 *
 * Because the fragments are inlined into the main component's template, they all
 * share the main component's scope (data, computed, methods) — no props needed.
 *
 * Fragment files (relative to the app root, which is the gui/ directory):
 *   tournament-templates/landing.html       - landing page (v-if="!tournamentState")
 *   tournament-templates/active.html        - active tournament view (v-else)
 *   tournament-templates/bracket-view.html  - bracket tree (inlined into active.html)
 *   tournament-templates/round-robin.html   - round robin view (inlined into active.html)
 *   tournament-templates/modals.html        - create + match-result modals
 */

const TEMPLATE_BASE_URL = 'tournament-templates/';

/**
 * Synchronously fetch a text file using XMLHttpRequest.
 * @param {string} path - URL path to the file
 * @returns {string} file contents
 */
function loadTextSync(path) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', path, false); // false = synchronous
    xhr.send(null);
    if (xhr.status !== 200 && xhr.status !== 0) {
        throw new Error(`Failed to load template ${path}: HTTP ${xhr.status}`);
    }
    return xhr.responseText;
}

/**
 * Load a single fragment, returning an empty string on failure so a missing
 * optional fragment doesn't take down the whole component.
 * @param {string} name - human-readable name for logging
 * @param {string} file - file name within the templates directory
 * @returns {string} fragment contents (or '' on error)
 */
function loadFragment(name, file) {
    const fullPath = TEMPLATE_BASE_URL + file;
    console.log(`[tournament-templates] Loading "${name}" from: ${fullPath}`);
    try {
        const content = loadTextSync(fullPath);
        console.log(`[tournament-templates] Loaded "${name}" successfully, length: ${content.length}`);
        return content;
    } catch (error) {
        console.error(`[tournament-templates] Could not load "${name}" (${fullPath}):`, error);
        return '';
    }
}

/**
 * Assemble the full tournament template from its fragments.
 * @returns {string} complete template string
 */
export function buildTournamentTemplate() {
    console.log('[tournament-templates] Building template...');
    const landing = loadFragment('landing', 'landing.html');
    const active = loadFragment('active', 'active.html');
    const bracketView = loadFragment('bracket-view', 'bracket-view.html');
    const roundRobin = loadFragment('round-robin', 'round-robin.html');
    const modals = loadFragment('modals', 'modals.html');

    console.log(`[tournament-templates] Fragments loaded: landing=${landing.length}, active=${active.length}, bracketView=${bracketView.length}, roundRobin=${roundRobin.length}, modals=${modals.length}`);

    // Inline the bracket tree and round-robin view into the active view.
    const activeAssembled = active
        .replace('{{BRACKET_VIEW}}', bracketView)
        .replace('{{ROUND_ROBIN}}', roundRobin);

    const result = `
<div class="tournament-page noscroll-flex flex-grow-1">
    <!-- Landing Page - Show when no tournament is active -->
    ${landing}

    <!-- Tournament Active -->
    ${activeAssembled}

    <!-- Modals -->
    ${modals}
</div>
`.trim();

    console.log(`[tournament-templates] Final template length: ${result.length}`);
    return result;
}
