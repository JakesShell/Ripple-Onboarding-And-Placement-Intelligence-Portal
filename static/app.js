const STORAGE_KEY = "rippleResult";
const RESPONSE_KEY = "rippleResponses";

document.addEventListener("DOMContentLoaded", () => {
    initializeAccessForms();
    initializeQuestionSequence();
    initializeProcessing();
    renderEmployeeResult();
    renderPlacementPath();
    addResetButton();
});


function alphaWords(text) {
    return (text || "").toLowerCase().match(/[a-zA-Z]{2,}/g) || [];
}

function looksLikeKeyboardNoise(text) {
    const joined = alphaWords(text).join("");
    const patterns = ["asdf", "qwer", "qwerty", "zxcv", "dfgdfg", "sdfg", "hjkl", "aaaa", "zzzz", "blah", "idk", "lolol"];

    if (patterns.includes(joined)) {
        return true;
    }

    if (patterns.some(pattern => joined.includes(pattern))) {
        return true;
    }

    if (joined.length >= 6 && new Set(joined).size <= 3) {
        return true;
    }

    return false;
}

function isMostlyRepeatedLetters(text) {
    const letters = (text || "").replace(/[^a-zA-Z]/g, "").toLowerCase();

    if (!letters) {
        return true;
    }

    const counts = {};
    for (const letter of letters) {
        counts[letter] = (counts[letter] || 0) + 1;
    }

    const highest = Math.max(...Object.values(counts));
    return highest / letters.length > 0.62;
}

function isMeaningfulClientResponse(text, chips) {
    const clean = (text || "").trim();
    const selectedChips = chips || [];

    // If the user typed anything, the typed answer must be meaningful.
    // A selected chip cannot turn random letters into a valid response.
    if (clean.length > 0) {
        const letters = clean.replace(/[^a-zA-Z]/g, "").toLowerCase();
        const words = alphaWords(clean);
        const uniqueWords = new Set(words);

        if (clean.length < 12) {
            return false;
        }

        if (words.length < 3) {
            return false;
        }

        if (uniqueWords.size < 2) {
            return false;
        }

        if (!letters || !/[aeiou]/.test(letters)) {
            return false;
        }

        if (isMostlyRepeatedLetters(clean)) {
            return false;
        }

        if (looksLikeKeyboardNoise(clean)) {
            return false;
        }

        const meaningfulWords = words.filter(word => word.length >= 3 && /[aeiou]/.test(word));

        if (meaningfulWords.length < 2) {
            return false;
        }

        if (new Set(meaningfulWords).size < 2) {
            return false;
        }

        return true;
    }

    // Blank response can only continue if the user selected enough signal chips.
    return selectedChips.length >= 2;
}

function showValidationMessage(anchor, message) {
    let note = document.getElementById("response-validation");

    if (!note) {
        note = document.createElement("p");
        note.id = "response-validation";
        note.className = "inline-validation";
        anchor.insertAdjacentElement("afterend", note);
    }

    note.textContent = message;
}

function clearValidationMessage() {
    const note = document.getElementById("response-validation");

    if (note) {
        note.textContent = "";
    }
}

function setInlineNote(afterElement, id, text) {
    if (!afterElement) {
        return;
    }

    let note = document.getElementById(id);

    if (!note) {
        note = document.createElement("p");
        note.id = id;
        note.className = "confidence-note";
        afterElement.insertAdjacentElement("afterend", note);
    }

    note.textContent = text;
}

function clearRippleSequence() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(RESPONSE_KEY);
    localStorage.removeItem("rippleEmployeeName");
    window.location.href = "/questions";
}

function addResetButton() {
    const target = document.querySelector(".sequence-actions") || document.querySelector(".result-actions");

    if (!target || document.getElementById("reset-sequence")) {
        return;
    }

    const button = document.createElement("button");
    button.id = "reset-sequence";
    button.className = "btn ghost reset-sequence";
    button.type = "button";
    button.textContent = "Start over";
    button.addEventListener("click", clearRippleSequence);
    target.appendChild(button);
}


function initializeAccessForms() {
    const employeeForm = document.getElementById("employee-access");

    if (!employeeForm) {
        return;
    }

    employeeForm.addEventListener("submit", () => {
        const name = document.getElementById("employee-name")?.value.trim();
        if (name) {
            localStorage.setItem("rippleEmployeeName", name);
        }
    });
}

function initializeQuestionSequence() {
    const root = document.getElementById("question-sequence");
    const questions = window.RIPPLE_QUESTIONS || [];

    if (!root || questions.length === 0) {
        return;
    }

    const divisionNumber = document.getElementById("division-number");
    const progressFill = document.getElementById("progress-fill");
    const divisionName = document.getElementById("division-name");
    const questionText = document.getElementById("question-text");
    const insightText = document.getElementById("insight-text");
    const responseInput = document.getElementById("response-input");
    const chipsContainer = document.getElementById("signal-chips");
    const backButton = document.getElementById("back-question");
    const nextButton = document.getElementById("next-question");
    const divisionItems = document.querySelectorAll(".division-list li");

    let step = 0;
    const saved = safeParse(localStorage.getItem(RESPONSE_KEY), []);
    const responses = questions.map((question, index) => saved[index] || {
        division: question.division,
        text: "",
        chips: []
    });

    function renderStep() {
        const current = questions[step];
        divisionNumber.textContent = `${String(step + 1).padStart(2, "0")} / ${questions.length}`;
        progressFill.style.width = `${((step + 1) / questions.length) * 100}%`;
        divisionName.textContent = current.division;
        questionText.textContent = current.question;
        insightText.textContent = current.insight;
        responseInput.value = responses[step].text || "";
        backButton.disabled = step === 0;
        nextButton.textContent = step === questions.length - 1 ? "Send" : "Next";

        divisionItems.forEach((item, index) => {
            item.classList.toggle("active", index === step);
        });

        chipsContainer.innerHTML = "";
        current.chips.forEach(chip => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "chip-button";
            button.textContent = chip;
            button.classList.toggle("selected", responses[step].chips.includes(chip));
            button.addEventListener("click", () => {
                const selected = responses[step].chips;
                if (selected.includes(chip)) {
                    responses[step].chips = selected.filter(item => item !== chip);
                } else {
                    responses[step].chips = [...selected, chip];
                }
                persistResponses();
                renderStep();
            });
            chipsContainer.appendChild(button);
        });
    }

    function persistCurrent() {
        responses[step] = {
            division: questions[step].division,
            text: responseInput.value.trim(),
            chips: responses[step].chips || []
        };
        persistResponses();
    }

    function persistResponses() {
        localStorage.setItem(RESPONSE_KEY, JSON.stringify(responses));
    }

    backButton.addEventListener("click", () => {
        persistCurrent();
        step = Math.max(0, step - 1);
        renderStep();
    });

    nextButton.addEventListener("click", async () => {
        persistCurrent();

        if (!isMeaningfulClientResponse(responses[step].text, responses[step].chips)) {
            responseInput.focus();
            showValidationMessage(responseInput, "Add a little more detail or choose a signal chip so RIPPLE has a real pattern to read.");
            return;
        }

        clearValidationMessage();

        if (step < questions.length - 1) {
            step += 1;
            renderStep();
            return;
        }

        try {
            const response = await fetch("/api/score", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({responses})
            });
            const data = await response.json();

            if (!response.ok) {
                showValidationMessage(responseInput, data.error || "RIPPLE needs a little more signal before it can generate a profile.");
                return;
            }

            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
            window.location.href = "/processing";
        } catch (error) {
            showValidationMessage(responseInput, "Unable to score the prototype sequence. Please try again.");
        }
    });

    responseInput.addEventListener("input", persistCurrent);
    renderStep();
}

function initializeProcessing() {
    const line = document.getElementById("processing-line");

    if (!line) {
        return;
    }

    const states = ["Interpreting patterns...", "Mapping tendencies...", "Preparing Ripple profile..."];
    let index = 0;
    const timer = setInterval(() => {
        index += 1;
        if (index < states.length) {
            line.textContent = states[index];
            return;
        }
        clearInterval(timer);
        window.location.href = "/results";
    }, 1000);
}

function renderEmployeeResult() {
    const target = document.getElementById("employee-result");

    if (!target) {
        return;
    }

    const result = getResult();

    if (!result) {
        return;
    }

    const profile = result.profile;
    document.getElementById("result-classification").textContent = result.classification;
    document.getElementById("operating-pattern").textContent = profile.operating_pattern;
    setInlineNote(
        document.getElementById("operating-pattern"),
        "confidence-note",
        `${result.confidenceLabel || "Prototype signal"} ? ${result.confidencePercent || 0}% prototype confidence based on keyword and signal-chip scoring.`
    );
    setInlineNote(
        document.getElementById("operating-pattern"),
        "confidence-note",
        `${result.confidenceLabel || "Prototype signal"} ? ${result.confidencePercent || 0}% prototype confidence based on keyword and signal-chip scoring.`
    );
    document.getElementById("work-best").textContent = profile.work_best;
    document.getElementById("onboarding-path").textContent = profile.onboarding_path;
    document.getElementById("growth-note").textContent = profile.growth_note;
    document.getElementById("model-reference").textContent = `Reserved model asset: static/${profile.model}`;
    document.getElementById("model-port").innerHTML = `<span>${escapeHtml(result.classification)}</span>`;
    fillList("strengths-list", profile.primary_strengths);
}

function renderPlacementPath() {
    const pathList = document.getElementById("path-list");

    if (!pathList) {
        return;
    }

    const result = getResult();

    if (!result) {
        pathList.innerHTML = `<p class="fine-print">No local result found. Complete the 10-question sequence first.</p>`;
        return;
    }

    document.getElementById("placement-classification").textContent = `${result.classification} placement map`;
    setInlineNote(
        document.getElementById("placement-classification"),
        "placement-confidence",
        `${result.confidenceLabel || "Prototype signal"} ? ${result.confidencePercent || 0}% prototype confidence based on keyword and signal-chip scoring.`
    );
    pathList.innerHTML = "";

    result.paths.forEach(path => {
        const row = document.createElement("article");
        row.className = "path-row";
        row.innerHTML = `
            <header>
                <strong>${escapeHtml(path.name)}</strong>
                <span>${path.percent}% aligned</span>
            </header>
            <div class="path-track">
                <div class="path-fill" style="width: ${path.percent}%"></div>
            </div>
            <p class="fine-print">Basis: ${escapeHtml(path.basis)}</p>
        `;
        pathList.appendChild(row);
    });
}

function fillList(elementId, items) {
    const list = document.getElementById(elementId);

    if (!list) {
        return;
    }

    list.innerHTML = "";
    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
    });
}

function getResult() {
    return safeParse(localStorage.getItem(STORAGE_KEY), null);
}

function safeParse(raw, fallback) {
    if (!raw) {
        return fallback;
    }

    try {
        return JSON.parse(raw);
    } catch (error) {
        return fallback;
    }
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}


/* --- RIPPLE 3D MODEL VIEWER HYDRATION --- */

(function () {
    const rippleModels = {
        architect: {
            label: "Architect",
            src: "/static/models/architect.glb",
            description: "Structure, systems, planning, and clarity."
        },
        current: {
            label: "Current",
            src: "/static/models/current.glb",
            description: "Action, speed, adaptability, and momentum."
        },
        signal: {
            label: "Signal",
            src: "/static/models/signal.glb",
            description: "People, communication, empathy, and social clarity."
        },
        spark: {
            label: "Spark",
            src: "/static/models/spark.glb",
            description: "Ideas, improvement, creativity, and possibility."
        },
        anchor: {
            label: "Anchor",
            src: "/static/models/anchor.glb",
            description: "Calm, steadiness, reliability, and support."
        }
    };

    function createModelViewer(key) {
        const model = rippleModels[key] || rippleModels.signal;

        const wrapper = document.createElement("div");
        wrapper.className = "ripple-3d-stage";
        wrapper.dataset.activeModel = key;

        wrapper.innerHTML = `
            <div class="ripple-model-orbit">
                <model-viewer
                    class="ripple-model-viewer"
                    environment-image="neutral"
                    src="${model.src}"
                    alt="${model.label} archetype model"
                    camera-controls
                    auto-rotate
                    rotation-per-second="18deg"
                    interaction-prompt="none"
                    exposure="0.62"
                    shadow-intensity="0.55"
                    camera-orbit="0deg 72deg 105%"
                    min-camera-orbit="auto 65deg auto"
                    max-camera-orbit="auto 82deg auto"
                    field-of-view="28deg">
                </model-viewer>
                <div class="ripple-model-glow"></div>
            </div>

            <div class="ripple-model-caption">
                <strong>${model.label}</strong>
                <span>${model.description}</span>
            </div>

            <div class="ripple-model-chips">
                ${Object.keys(rippleModels).map(item => `
                    <button type="button" class="ripple-model-chip ${item === key ? "active" : ""}" data-model-key="${item}">
                        ${rippleModels[item].label}
                    </button>
                `).join("")}
            </div>
        `;

        wrapper.querySelectorAll(".ripple-model-chip").forEach(button => {
            button.addEventListener("click", () => {
                const selected = button.dataset.modelKey;
                const selectedModel = rippleModels[selected];

                wrapper.dataset.activeModel = selected;
                wrapper.querySelector(".ripple-model-viewer").setAttribute("src", selectedModel.src);
                wrapper.querySelector(".ripple-model-viewer").setAttribute("alt", `${selectedModel.label} archetype model`);
                wrapper.querySelector(".ripple-model-caption strong").textContent = selectedModel.label;
                wrapper.querySelector(".ripple-model-caption span").textContent = selectedModel.description;

                wrapper.querySelectorAll(".ripple-model-chip").forEach(chip => {
                    chip.classList.toggle("active", chip.dataset.modelKey === selected);
                });
            });
        });

        return wrapper;
    }

    function findPlaceholderContainer() {
        const fileNames = ["architect.glb", "current.glb", "signal.glb", "spark.glb", "anchor.glb"];
        const nodes = Array.from(document.querySelectorAll("body *")).filter(node => {
            const text = (node.textContent || "").trim().toLowerCase();
            return fileNames.includes(text);
        });

        if (nodes.length < 3) {
            return null;
        }

        const containers = new Map();

        nodes.forEach(node => {
            let parent = node.parentElement;

            for (let i = 0; i < 4 && parent; i += 1) {
                const text = (parent.textContent || "").toLowerCase();
                const matches = fileNames.filter(name => text.includes(name)).length;

                if (matches >= 3) {
                    containers.set(parent, matches);
                    break;
                }

                parent = parent.parentElement;
            }
        });

        return Array.from(containers.keys())[0] || null;
    }

    function hydratePlaceholderModels() {
        const container = findPlaceholderContainer();

        if (!container || container.dataset.modelHydrated === "true") {
            return;
        }

        container.dataset.modelHydrated = "true";
        container.innerHTML = "";
        container.appendChild(createModelViewer("signal"));
    }

    function getResultModelKey() {
        try {
            const result = JSON.parse(localStorage.getItem("rippleResult") || "{}");
            const classification = String(result.classification || "signal").toLowerCase();
            return rippleModels[classification] ? classification : "signal";
        } catch {
            return "signal";
        }
    }

    function hydrateResultModel() {
        const possibleHosts = [
            ".result-model",
            ".profile-model",
            ".archetype-model",
            ".result-orb",
            ".profile-orb",
            ".model-orb"
        ];

        const host = possibleHosts
            .map(selector => document.querySelector(selector))
            .find(Boolean);

        if (!host || host.dataset.modelHydrated === "true") {
            return;
        }

        host.dataset.modelHydrated = "true";
        host.innerHTML = "";
        host.appendChild(createModelViewer(getResultModelKey()));
    }

    function hydrateWelcomeModel() {
        const pageText = document.body.textContent || "";
        const isWelcome = pageText.includes("Before placement") || pageText.includes("work pattern should feel seen");

        if (!isWelcome) {
            return;
        }

        hydratePlaceholderModels();
    }

    document.addEventListener("DOMContentLoaded", () => {
        hydratePlaceholderModels();
        hydrateWelcomeModel();
        hydrateResultModel();
    });
})();
