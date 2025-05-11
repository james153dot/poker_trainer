/**
 * main.js
 * -------
 * Single ES‑module entry loaded by BOTH index.html (Play) and quiz.html.
 * Detects which page we are on via presence of sentinel DOM elements and
 * initialises only relevant handlers — avoiding separate bundles.
 *
 * Functions / Sections:
 *   1. Utilities   – tiny helper wrappers
 *   2. Card grid   – render deck once DOM ready
 *   3. PLAY PAGE   – solve workflow + history
 *   4. QUIZ PAGE   – question cycle + history
 */

import {
    renderDeck,
    getSelected
} from "./cardpicker.js";

/* ---------- 1. Utilities ------------------------------------------------ */
function qs(id) {
    return document.getElementById(id);
}

/* ---------- 2. Render 52‑card grid once DOM is ready -------------------- */
document.addEventListener("DOMContentLoaded", () => {
    const grid = qs("card-grid");
    if (grid) renderDeck(grid);
});

/* ========================================================================
   3. PLAY MODE LOGIC
   ====================================================================== */
if (qs("solve-btn")) { // sentinel: only exists on Play page

    /* enable/disable Solve button when selection changes */
    document.addEventListener("cardSelectionChanged", () => {
        const sel = getSelected();
        qs("chosen").textContent = "Selected: " + (sel.join(", ") || "—");
        qs("solve-btn").disabled = sel.length !== 2;
    });

    /* click handler – gather inputs, POST to /api/solve, render result */
    qs("solve-btn").onclick = async () => {
        const payload = {
            hero_cards: getSelected(),
            pot_size: +qs("pot").value,
            facing_bet: +qs("bet").value,
            num_villains: +qs("villains").value,
            position: qs("pos").value,
            street: qs("street").value,
            board_cards: [] // future feature
        };

        // POST → /api/solve
        const res = await fetch("/api/solve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }).then(r => r.json());

        // Show advice block
        qs("result").classList.remove("hidden");
        qs("advice-text").textContent =
            `Action: ${res.advice.toUpperCase()}` +
            (res.raise_size ? ` ($${res.raise_size})` : "");
        qs("equity-text").textContent =
            `Equity ${(res.equity * 100).toFixed(1)} %  |  ` +
            `Pot-odds ${(res.pot_odds * 100).toFixed(1)} %`;

        loadHist(); // refresh Play history list
    };

    /* helper – fetch last 30 hands and render into <ul> */
    async function loadHist() {
        const hist = await fetch("/api/history").then(r => r.json());
        const ul = qs("hist-list");
        ul.innerHTML = "";

        hist.forEach(h => {
            const li = document.createElement("li");

            // Build a verbose, human-readable summary
            li.textContent =
                `${h.hero_cards} | pot $${h.pot_size} facing $${h.facing_bet} ` +
                `| ${h.num_villains} villain${h.num_villains > 1 ? "s" : ""} ` +
                `| ${h.position} ${h.street} ` +
                `⇒ ${h.advice_action.toUpperCase()}` +
                (h.raise_size ? ` $${h.raise_size}` : "");

            ul.appendChild(li);
        });
    }

}

/* ========================================================================
   4. QUIZ MODE LOGIC
   ====================================================================== */
if (qs("quiz-box")) { // sentinel: only exists on Quiz page
    const handP = qs("quiz-hand"); // paragraph showing scenario
    const feedback = qs("quiz-feedback"); // paragraph for ✅/❌ text

    // ---------------- helper: fetch + display next quiz hand -------------
    async function nextQuiz() {
        handP.textContent = "Loading…";
        feedback.textContent = "";
        const res = await fetch("/api/quiz/next");
        if (!res.ok) { // empty DB case
            handP.textContent = "No quiz hands in database!";
            return;
        }
        const row = await res.json();
        window.currentQuiz = row; // store globally for click handler

        handP.textContent =
            `Hand: ${row.hero_cards}   Pot $${row.pot_size} facing $${row.facing_bet}`;
    }

    // ---------------- helper: refresh quiz history list ------------------
    async function loadQuizHist() {
        const list = qs("quiz-hist-list");
        if (!list) return;
        const hist = await fetch("/api/quiz/history").then(r => r.json());
        list.innerHTML = "";
        hist.forEach(h => {
            const li = document.createElement("li");
            li.textContent =
                `${h.hero_cards} (${h.position}) — ` +
                `you ${h.user_action.toUpperCase()} ` +
                `| solver ${h.advice_action.toUpperCase()} ` +
                (h.correct ? "✅" : "❌");
            list.appendChild(li);
        });
    }

    // ---------------- attach button handlers -----------------------------
    document.querySelectorAll("#quiz-btns button").forEach(btn => {
        btn.onclick = async () => {
            const row = window.currentQuiz;
            if (!row) return; // race‑condition guard

            // POST answer to server
            const resp = await fetch("/api/quiz/answer", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id: row.id,
                    user_action: btn.dataset.act
                })
            }).then(r => r.json());

            // Show feedback to user
            feedback.textContent = resp.correct ?
                "✅ Correct!" :
                `❌ Wrong. Solver suggested ${resp.solver}`;

            // after short delay → next hand + history refresh
            setTimeout(() => {
                nextQuiz();
                loadQuizHist();
            }, 1500);
        };
    });

    // --------------- kick‑off first hand + history load ------------------
    nextQuiz();
    loadQuizHist();
}
