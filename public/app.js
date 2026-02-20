// FinSpeak Frontend Application

const API_BASE = '/api';

// DOM Elements
const queryInput = document.getElementById('queryInput');
const submitBtn = document.getElementById('submitBtn');
const micBtn = document.getElementById('micBtn');
const listeningIndicator = document.getElementById('listeningIndicator');
const responseCard = document.getElementById('responseCard');
const errorCard = document.getElementById('errorCard');
const loadingCard = document.getElementById('loadingCard');
const intentBadge = document.getElementById('intentBadge');
const answerText = document.getElementById('answerText');
const dataDetails = document.getElementById('dataDetails');
const errorText = document.getElementById('errorText');
const speakBtn = document.getElementById('speakBtn');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');
const langSelect = document.getElementById('langSelect');
const learnInput = document.getElementById('learnInput');
const learnBtn = document.getElementById('learnBtn');
const learnMicBtn = document.getElementById('learnMicBtn');
const learnListeningIndicator = document.getElementById('learnListeningIndicator');
const learnCard = document.getElementById('learnCard');
const learnTerm = document.getElementById('learnTerm');
const learnText = document.getElementById('learnText');
const learnSource = document.getElementById('learnSource');
const learnSpeakBtn = document.getElementById('learnSpeakBtn');

// State
let isListening = false;
let speechRecognizer = null;
let currentAudio = null;

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    // Event listeners - Query
    submitBtn.addEventListener('click', handleQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleQuery();
    });
    
    // Voice
    micBtn.addEventListener('click', toggleListening);
    speakBtn.addEventListener('click', () => speakText(answerText.textContent));
    
    // Search
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Learn Mode
    learnBtn.addEventListener('click', handleLearn);
    learnInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLearn();
    });
    learnSpeakBtn.addEventListener('click', () => speakText(learnText.textContent));
    learnMicBtn.addEventListener('click', startLearnListening);

    // Example buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            queryInput.value = btn.dataset.query;
            handleQuery();
        });
    });

    // Learn chips
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            learnInput.value = chip.dataset.term;
            handleLearn();
        });
    });
}

function getLanguage() {
    const val = langSelect.value;
    // For Hinglish, use Hindi speech recognition (best available)
    if (val === 'hinglish') return 'hi-IN';
    return val;
}

function getLangShort() {
    const val = langSelect.value;
    if (val === 'hinglish') return 'hinglish';
    if (val.startsWith('hi')) return 'hi';
    return 'en';
}

// ---- QUERY ----

async function handleQuery() {
    const query = queryInput.value.trim();
    if (!query) return;

    showLoading();
    hideError();
    hideResponse();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: query, language: getLangShort() })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            // If the backend detected an explain/learn intent, show in Learn card
            if (data.intent === 'explain') {
                showLearnResult(data);
            } else {
                showResponse(data);
            }
        } else {
            showError(data.message || 'Query failed');
        }
    } catch (error) {
        hideLoading();
        showError('Failed to connect to server: ' + error.message);
    }
}

function showResponse(data) {
    responseCard.classList.remove('hidden');
    
    const intent = data.intent || 'info';
    intentBadge.textContent = intent.replace('get_', '').replace('_', ' ');
    intentBadge.className = 'badge ' + (intent.includes('nav') ? 'nav' : 'returns');
    
    answerText.textContent = data.answer;
    
    if (data.data) {
        let html = '';
        const d = data.data;
        if (d.fund_name) html += `<p><span class="label">Fund:</span> ${d.fund_name}</p>`;
        if (d.fund_house) html += `<p><span class="label">Fund House:</span> ${d.fund_house}</p>`;
        if (d.nav !== undefined) html += `<p><span class="label">NAV:</span> ₹${d.nav}</p>`;
        if (d.date) html += `<p><span class="label">Date:</span> ${d.date}</p>`;
        if (d.returns_percent !== undefined) html += `<p><span class="label">Returns:</span> ${d.returns_percent}%</p>`;
        if (d.period_months) html += `<p><span class="label">Period:</span> ${d.period_months} months</p>`;
        dataDetails.innerHTML = html;
    }
    
    // Auto-speak the response
    speakText(data.answer);
}

function showLearnResult(data) {
    // Show the explanation in the Learn Mode card (scrolls to it)
    learnCard.classList.remove('hidden');
    learnTerm.textContent = (data.data?.term || '').toUpperCase();
    learnText.textContent = data.answer;
    learnSource.textContent = data.data?.source === 'ai' ? '✨ AI-generated' : '📖 Curated';
    
    // Scroll to learn section
    learnCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Auto-speak the explanation
    speakText(data.answer);
}

function hideResponse() { responseCard.classList.add('hidden'); }
function showError(msg) { errorCard.classList.remove('hidden'); errorText.textContent = msg; }
function hideError() { errorCard.classList.add('hidden'); }
function showLoading() { loadingCard.classList.remove('hidden'); }
function hideLoading() { loadingCard.classList.add('hidden'); }

// ---- SPEECH RECOGNITION (multilingual) ----

function toggleListening() {
    if (isListening) { stopListening(); } else { startListening(); }
}

function startListening() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showError('Speech recognition not supported. Use Chrome or Edge.');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = false;
    speechRecognizer.interimResults = false;
    speechRecognizer.lang = getLanguage(); // Multilingual!

    speechRecognizer.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        listeningIndicator.classList.remove('hidden');
    };

    speechRecognizer.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        queryInput.value = transcript;
        stopListening();
        handleQuery();
    };

    speechRecognizer.onerror = (event) => {
        stopListening();
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            showError('Speech error: ' + event.error);
        }
    };

    speechRecognizer.onend = () => { stopListening(); };
    speechRecognizer.start();
}

function stopListening() {
    isListening = false;
    micBtn.classList.remove('listening');
    listeningIndicator.classList.add('hidden');
    if (speechRecognizer) {
        try { speechRecognizer.stop(); } catch (e) {}
        speechRecognizer = null;
    }
}

// ---- TEXT-TO-SPEECH (Azure Neural Voice with browser fallback) ----

async function speakText(text) {
    if (!text) return;
    
    // Stop any currently playing audio
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    window.speechSynthesis?.cancel();
    
    // Try Azure Neural TTS first (natural voices)
    try {
        const response = await fetch(`${API_BASE}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, language: getLanguage() })
        });
        
        const data = await response.json();
        
        if (data.success && data.audio_base64) {
            const audioBytes = atob(data.audio_base64);
            const audioArray = new Uint8Array(audioBytes.length);
            for (let i = 0; i < audioBytes.length; i++) {
                audioArray[i] = audioBytes.charCodeAt(i);
            }
            const blob = new Blob([audioArray], { type: 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            
            currentAudio = new Audio(url);
            currentAudio.play();
            currentAudio.onended = () => { URL.revokeObjectURL(url); currentAudio = null; };
            return;
        }
    } catch (e) {
        console.log('Azure TTS unavailable, using browser voice');
    }
    
    // Fallback to browser TTS
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = getLanguage();
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }
}

// ---- LEARN MODE ----

let learnRecognizer = null;

function startLearnListening() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showError('Speech recognition not supported. Use Chrome or Edge.');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    learnRecognizer = new SpeechRecognition();
    learnRecognizer.continuous = false;
    learnRecognizer.interimResults = false;
    learnRecognizer.lang = getLanguage();

    learnRecognizer.onstart = () => {
        learnMicBtn.classList.add('listening');
        learnListeningIndicator.classList.remove('hidden');
    };

    learnRecognizer.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        learnInput.value = transcript;
        stopLearnListening();
        handleLearn();
    };

    learnRecognizer.onerror = (event) => {
        stopLearnListening();
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            showError('Speech error: ' + event.error);
        }
    };

    learnRecognizer.onend = () => { stopLearnListening(); };
    learnRecognizer.start();
}

function stopLearnListening() {
    learnMicBtn.classList.remove('listening');
    learnListeningIndicator.classList.add('hidden');
    if (learnRecognizer) {
        try { learnRecognizer.stop(); } catch (e) {}
        learnRecognizer = null;
    }
}

async function handleLearn() {
    const term = learnInput.value.trim();
    if (!term) return;

    learnCard.classList.remove('hidden');
    learnText.textContent = 'Loading explanation...';
    learnTerm.textContent = '';
    learnSource.textContent = '';

    try {
        const response = await fetch(`${API_BASE}/explain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ term, language: getLangShort() })
        });

        const data = await response.json();

        if (data.success) {
            learnTerm.textContent = data.term.toUpperCase();
            learnText.textContent = data.explanation;
            learnSource.textContent = data.source === 'ai' ? '✨ AI-generated' : '📖 Curated';
            // Auto-speak the explanation
            speakText(data.explanation);
        } else {
            learnText.textContent = data.message || 'No explanation found.';
        }
    } catch (error) {
        learnText.textContent = 'Failed to load explanation.';
    }
}

// ---- SEARCH ----

async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        if (data.success && data.funds?.length > 0) {
            let html = '<ul>';
            data.funds.forEach(fund => {
                html += `
                    <li onclick="selectFund('${fund.name.replace(/'/g, "\\'")}')">
                        <div class="fund-code">${fund.code}</div>
                        <div class="fund-name">${fund.name}</div>
                    </li>`;
            });
            html += '</ul>';
            searchResults.innerHTML = html;
            searchResults.classList.remove('hidden');
        } else {
            searchResults.innerHTML = '<p style="color: #8892b0;">No funds found</p>';
            searchResults.classList.remove('hidden');
        }
    } catch (error) {
        showError('Search failed: ' + error.message);
    }
}

window.selectFund = function(fundName) {
    queryInput.value = `What is the NAV of ${fundName}?`;
    handleQuery();
    searchResults.classList.add('hidden');
};
