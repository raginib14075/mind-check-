/**
 * MindCheck Bot - Minimalist App Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
    // App State
    let appConfig = null;
    let userName = "Guest";
    let selectedMode = 1;
    let qCount = 9;

    let chatQuestions = [];
    let chatIndex = 0;
    let chatHistory = [];
    let cueBank = {};

    let quizQuestions = [];
    let quizAnswers = {}; // { qid: score }

    // DOM Elements
    const stageSetup = document.getElementById('stageSetup');
    const stageChat = document.getElementById('stageChat');
    const stageQuiz = document.getElementById('stageQuiz');
    const stageReport = document.getElementById('stageReport');

    const setupForm = document.getElementById('setupForm');
    const userNameInput = document.getElementById('userNameInput');
    const modePills = document.querySelectorAll('.mode-pill');

    const chatLog = document.getElementById('chatLog');
    const chatTextInput = document.getElementById('chatTextInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const chatInputRow = document.getElementById('chatInputRow');
    const chatNextBox = document.getElementById('chatNextBox');
    const proceedToQuizBtn = document.getElementById('proceedToQuizBtn');

    const questionsFeed = document.getElementById('questionsFeed');
    const quizProgressText = document.getElementById('quizProgressText');
    const submitAssessmentBtn = document.getElementById('submitAssessmentBtn');

    const reportUserNameTitle = document.getElementById('reportUserNameTitle');
    const reportScoreVal = document.getElementById('reportScoreVal');
    const reportScoreMax = document.getElementById('reportScoreMax');
    const reportSeverityTag = document.getElementById('reportSeverityTag');
    const reportPatternText = document.getElementById('reportPatternText');
    const catList = document.getElementById('catList');
    const cuesTags = document.getElementById('cuesTags');
    const convoCuesBox = document.getElementById('convoCuesBox');
    const restartAppBtn = document.getElementById('restartAppBtn');
    const crisisModal = document.getElementById('crisisModal');

    // Fetch Config
    async function init() {
        try {
            const res = await fetch('/api/config');
            appConfig = await res.json();
            chatQuestions = appConfig.intro_questions || [];
        } catch (e) {
            console.error("Failed to load server config", e);
        }
    }
    await init();

    function setStage(stageId) {
        [stageSetup, stageChat, stageQuiz, stageReport].forEach(s => s.classList.remove('active'));
        document.getElementById(stageId).classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- SETUP STAGE ---
    modePills.forEach(pill => {
        pill.addEventListener('click', () => {
            modePills.forEach(p => p.classList.remove('selected'));
            pill.classList.add('selected');
            selectedMode = parseInt(pill.dataset.mode);
            qCount = parseInt(pill.dataset.count);
        });
    });

    setupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        userName = userNameInput.value.trim() || "Guest";
        setStage('stageChat');
        startChatStage();
    });


    // --- CHAT STAGE ---
    function startChatStage() {
        chatLog.innerHTML = '';
        chatHistory = [];
        chatIndex = 0;
        cueBank = {};
        chatInputRow.classList.remove('hidden');
        chatNextBox.classList.add('hidden');

        addChatBubble('bot', `Hello ${userName}. Let's start with a gentle conversational check-in.`);
        setTimeout(() => askNextChatQuestion(), 400);
    }

    function askNextChatQuestion() {
        if (chatIndex < chatQuestions.length) {
            addChatBubble('bot', chatQuestions[chatIndex]);
        } else {
            chatInputRow.classList.add('hidden');
            chatNextBox.classList.remove('hidden');
        }
    }

    function addChatBubble(sender, text) {
        const row = document.createElement('div');
        row.className = `chat-bubble-row ${sender}`;
        row.innerHTML = `<div class="chat-msg-bubble">${escapeHtml(text)}</div>`;
        chatLog.appendChild(row);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    async function handleChatSubmit() {
        const text = chatTextInput.value.trim();
        if (!text) return;

        addChatBubble('user', text);
        chatTextInput.value = '';
        chatHistory.push(text);

        try {
            const checkRes = await fetch('/api/check-safety', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const sData = await checkRes.json();
            if (sData.is_crisis) {
                crisisModal.classList.remove('hidden');
            }
        } catch (e) {
            console.error("Safety check error", e);
        }

        chatIndex++;
        setTimeout(() => askNextChatQuestion(), 400);
    }

    chatSendBtn.addEventListener('click', handleChatSubmit);
    chatTextInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleChatSubmit();
        }
    });

    proceedToQuizBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/analyze-intro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory })
            });
            const introAnalysis = await res.json();
            cueBank = introAnalysis.cue_bank || {};
        } catch (e) {
            console.error("Intro analysis error", e);
        }

        setStage('stageQuiz');
        buildQuestionnaireFeed();
    });


    // --- QUESTIONNAIRE FEED STAGE ---
    function buildQuestionnaireFeed() {
        quizQuestions = appConfig.master_questions.slice(0, qCount);
        quizAnswers = {};
        questionsFeed.innerHTML = '';
        updateSubmitBar();

        const ratingLabels = [
            { score: 0, label: '0 · Not at all' },
            { score: 1, label: '1 · Several days' },
            { score: 2, label: '2 · Half the days' },
            { score: 3, label: '3 · Nearly every day' }
        ];

        quizQuestions.forEach((q, index) => {
            const card = document.createElement('div');
            card.className = 'q-card';
            card.dataset.qid = q.id;

            card.innerHTML = `
                <div class="q-card-meta">Question ${index + 1} of ${quizQuestions.length} — last two weeks</div>
                <div class="q-card-text">${escapeHtml(q.text)}</div>
                <div class="q-rating-row">
                    ${ratingLabels.map(r => `
                        <button type="button" class="q-rating-pill" data-score="${r.score}">
                            ${r.label}
                        </button>
                    `).join('')}
                </div>
            `;

            // Event listeners for rating pills
            const pills = card.querySelectorAll('.q-rating-pill');
            pills.forEach(pill => {
                pill.addEventListener('click', () => {
                    const score = parseInt(pill.dataset.score);
                    quizAnswers[q.id] = score;

                    pills.forEach(p => p.classList.remove('selected'));
                    pill.classList.add('selected');

                    updateSubmitBar();
                });
            });

            questionsFeed.appendChild(card);
        });
    }

    function updateSubmitBar() {
        const answeredCount = Object.keys(quizAnswers).length;
        const total = quizQuestions.length;
        quizProgressText.textContent = `${answeredCount} of ${total} answered`;

        submitAssessmentBtn.disabled = answeredCount < total;
    }

    submitAssessmentBtn.addEventListener('click', async () => {
        setStage('stageReport');
        reportUserNameTitle.textContent = `Summary for ${userName}`;

        try {
            const res = await fetch('/api/submit-assessment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_name: userName,
                    answers: quizAnswers,
                    q_count: qCount,
                    cue_bank: cueBank
                })
            });

            const data = await res.json();

            reportScoreVal.textContent = data.total_score;
            reportScoreMax.textContent = `/ ${data.max_score}`;
            reportSeverityTag.textContent = data.severity;
            reportPatternText.textContent = data.pattern;

            // Category breakdown
            catList.innerHTML = '';
            if (data.category_scores) {
                Object.entries(data.category_scores).forEach(([cat, score]) => {
                    const item = document.createElement('div');
                    item.className = 'cat-item';
                    item.innerHTML = `
                        <span>${capitalize(cat)}</span>
                        <strong>${score} pts</strong>
                    `;
                    catList.appendChild(item);
                });
            }

            // Keyword Cues
            cuesTags.innerHTML = '';
            if (data.convo_notes && data.convo_notes.length > 0) {
                convoCuesBox.classList.remove('hidden');
                data.convo_notes.forEach(note => {
                    const tag = document.createElement('span');
                    tag.className = 'cue-pill';
                    tag.textContent = note;
                    cuesTags.appendChild(tag);
                });
            } else {
                convoCuesBox.classList.add('hidden');
            }

        } catch (e) {
            console.error("Error submitting assessment", e);
        }
    });

    restartAppBtn.addEventListener('click', () => {
        setStage('stageSetup');
    });

    function escapeHtml(text) {
        return text.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m]));
    }

    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
});
