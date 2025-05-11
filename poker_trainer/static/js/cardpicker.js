// cardpicker.js
// -------------
// FE component that renders a 52‑card mini‑grid and allows exactly two
// selections. Emits a custom DOM event `cardSelectionChanged` on every toggle.

// ---------------- Constants -----------------------------------------------
const ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]; // high→low
const suits = [{
        c: "s",
        sym: "♠"
    }, // Spades   – black
    {
        c: "h",
        sym: "♥",
        red: true
    }, // Hearts   – red
    {
        c: "d",
        sym: "♦",
        red: true
    }, // Diamonds – red
    {
        c: "c",
        sym: "♣"
    } // Clubs    – black
];

// --------------------------------------------------------------------------
// renderDeck(gridEl)
// Renders 52 div.card nodes in rank‑major order into gridEl.
// --------------------------------------------------------------------------
export function renderDeck(gridEl) {
    const frag = document.createDocumentFragment(); // build off‑DOM for perf
    suits.forEach(s => {
        ranks.forEach(r => {
            const div = document.createElement("div");
            div.className = "card" + (s.red ? " red" : "");
            div.dataset.card = r + s.c; // e.g. "As", "Td"
            div.textContent = r + s.sym; // user‐friendly text
            div.onclick = () => toggle(div);
            frag.appendChild(div);
        });
    });
    gridEl.appendChild(frag);
}

// --------------------------------------------------------------------------
// toggle(el) – select/unselect card div
//   • Only allow TWO cards selected at any time
//   • After mutation emit custom event so main.js can react
// --------------------------------------------------------------------------
function toggle(el) {
    if (el.classList.contains("selected")) {
        el.classList.remove("selected");
    } else {
        // Guard: max 2 selections
        if (document.querySelectorAll(".card.selected").length >= 2) return;
        el.classList.add("selected");
    }
    // Broadcast state change
    document.dispatchEvent(new CustomEvent("cardSelectionChanged"));
}

// --------------------------------------------------------------------------
// getSelected() – returns array of strings like ["Ah","Kd"]
// --------------------------------------------------------------------------
export function getSelected() {
    return [...document.querySelectorAll(".card.selected")]
        .map(el => el.dataset.card);
}
