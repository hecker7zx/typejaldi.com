/**
 * TypeJaldi.com - Premium Typing Engine
 * Enhanced with GSAP for fluid animations and micro-interactions.
 */

// ──────────────────────────────────────
// CONFIGURATION & STATE
// ──────────────────────────────────────

const CONFIG = {
    TOTAL_WORDS: 100,
    DEFAULT_TIME: 30,
    XP_PER_WPM: 1.2,
    XP_PER_ACC: 2.0,
    LEVELS: [
        { level: 1, xp: 0, title: 'Doodle Beginner' },
        { level: 2, xp: 100, title: 'Sketch Apprentice' },
        { level: 3, xp: 300, title: 'Ink Scratcher' },
        { level: 4, xp: 600, title: 'Pencil Master' },
        { level: 5, xp: 1000, title: 'Pen Artist' }
    ]
};

let state = {
    words: [],
    currentIndex: 0,
    currentInput: '',
    startTime: null,
    timer: CONFIG.DEFAULT_TIME,
    isActive: false,
    isFinished: false,
    stats: {
        wpm: 0,
        accuracy: 100,
        correctChars: 0,
        totalChars: 0,
        streak: 0,
        bestStreak: 0
    },
    user: {
        totalXP: 0,
        level: 1,
        bestWPM: 0
    }
};

// ──────────────────────────────────────
// WORD LISTS
// ──────────────────────────────────────

const WORD_LISTS = {
    common: ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'great', 'been', 'still', 'place', 'where', 'part', 'every', 'such', 'much', 'again', 'own', 'found', 'those', 'never', 'under', 'last', 'while', 'house', 'world', 'life', 'hand', 'here', 'thought', 'long', 'little', 'man', 'both', 'home', 'write', 'read', 'book', 'love', 'bird', 'tree', 'moon', 'star', 'water'],
    // Add more if needed, or keep it simple for the demo
};

// ──────────────────────────────────────
// INITIALIZATION
// ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
    animateEntrance();
});

function initApp() {
    generateWords();
    renderWords();
    loadProgress();
    updateUI();
    lucide.createIcons();
}

function generateWords() {
    const pool = WORD_LISTS.common;
    state.words = Array.from({ length: CONFIG.TOTAL_WORDS }, () => 
        pool[Math.floor(Math.random() * pool.length)]
    );
}

function renderWords() {
    const container = document.getElementById('wordDisplayInner');
    if (!container) return;
    
    container.innerHTML = state.words.map((word, i) => `
        <span class="word ${i === 0 ? 'current' : ''}" data-index="${i}">${word}</span>
    `).join('');
    
    updateCaret();
}

// ──────────────────────────────────────
// CORE LOGIC
// ──────────────────────────────────────

function handleInput(e) {
    if (state.isFinished) return;
    
    if (!state.isActive) {
        startTest();
    }

    const val = e.target.value;
    
    if (val.endsWith(' ')) {
        submitWord(val.trim());
        e.target.value = '';
    } else {
        state.currentInput = val;
        updateLiveFeedback();
    }
}

function startTest() {
    state.isActive = true;
    state.startTime = Date.now();
    
    const timerInterval = setInterval(() => {
        state.timer--;
        updateUI();
        
        if (state.timer <= 0) {
            clearInterval(timerInterval);
            endTest();
        }
    }, 1000);

    // GSAP: Subtle pulse on the notebook when active
    gsap.to('.notebook', {
        boxShadow: '0 20px 60px rgba(255, 93, 0, 0.15)',
        duration: 1,
        repeat: -1,
        yoyo: true
    });
}

function submitWord(input) {
    const target = state.words[state.currentIndex];
    const isCorrect = input === target;
    
    const wordEl = document.querySelector(`.word[data-index="${state.currentIndex}"]`);
    
    if (isCorrect) {
        wordEl.classList.add('correct');
        state.stats.correctChars += target.length + 1;
        state.stats.streak++;
        if (state.stats.streak > state.stats.bestStreak) state.stats.bestStreak = state.stats.streak;
        
        // GSAP: Pop animation for correct word
        gsap.fromTo(wordEl, { scale: 1.2 }, { scale: 1, duration: 0.3, ease: 'back.out' });
        createParticles(wordEl);
    } else {
        wordEl.classList.add('incorrect');
        state.stats.streak = 0;
        
        // GSAP: Shake animation for error
        gsap.to('.notebook', { x: 5, duration: 0.05, repeat: 5, yoyo: true, onComplete: () => gsap.set('.notebook', { x: 0 }) });
    }
    
    wordEl.classList.remove('current');
    state.currentIndex++;
    state.currentInput = '';
    
    const nextWord = document.querySelector(`.word[data-index="${state.currentIndex}"]`);
    if (nextWord) {
        nextWord.classList.add('current');
        scrollToWord(nextWord);
    }
    
    updateStats();
    updateCaret();
}

function updateLiveFeedback() {
    const target = state.words[state.currentIndex];
    const wordEl = document.querySelector(`.word[data-index="${state.currentIndex}"]`);
    if (!wordEl) return;

    let html = '';
    for (let i = 0; i < Math.max(target.length, state.currentInput.length); i++) {
        const tChar = target[i] || '';
        const iChar = state.currentInput[i] || '';
        
        if (i < state.currentInput.length) {
            if (tChar === iChar) {
                html += `<span class="text-success">${tChar}</span>`;
            } else {
                html += `<span class="text-error">${iChar || tChar}</span>`;
            }
        } else {
            html += `<span>${tChar}</span>`;
        }
    }
    wordEl.innerHTML = html;
    updateCaret();
}

function updateStats() {
    const elapsed = (Date.now() - state.startTime) / 60000;
    state.stats.wpm = Math.round((state.stats.correctChars / 5) / elapsed) || 0;
    
    // Smoothly update stat displays
    gsap.to('#wpmDisplay', { innerText: state.stats.wpm, duration: 0.5, snap: { innerText: 1 } });
}

// ──────────────────────────────────────
// UI & ANIMATIONS
// ──────────────────────────────────────

function animateEntrance() {
    gsap.from('.notebook', {
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
        delay: 0.2
    });
    
    gsap.from('.logo', {
        x: -50,
        opacity: 0,
        duration: 1,
        ease: 'back.out',
        delay: 0.5
    });

    gsap.from('.stat-card', {
        scale: 0.8,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'back.out',
        delay: 0.8
    });
}

function createParticles(el) {
    const rect = el.getBoundingClientRect();
    const colors = ['#ff5d00', '#3d8b5e', '#4a7fb5'];
    
    for (let i = 0; i < 8; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        document.body.appendChild(p);
        
        const size = Math.random() * 6 + 4;
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        gsap.set(p, {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2,
            width: size,
            height: size,
            backgroundColor: color
        });
        
        gsap.to(p, {
            x: '+=' + (Math.random() - 0.5) * 100,
            y: '+=' + (Math.random() - 0.5) * 100,
            opacity: 0,
            scale: 0,
            duration: 0.6 + Math.random() * 0.4,
            ease: 'power2.out',
            onComplete: () => p.remove()
        });
    }
}

function updateCaret() {
    const currentWord = document.querySelector('.word.current');
    const caret = document.getElementById('caret') || createCaret();
    
    if (currentWord) {
        const rect = currentWord.getBoundingClientRect();
        const containerRect = document.getElementById('wordDisplayInner').getBoundingClientRect();
        
        // Simplified caret positioning logic
        // In a real app, you'd calculate based on character width
        gsap.to(caret, {
            left: currentWord.offsetLeft + (state.currentInput.length * 12), // approximate
            top: currentWord.offsetTop,
            duration: 0.1
        });
    }
}

function createCaret() {
    const caret = document.createElement('div');
    caret.id = 'caret';
    caret.className = 'caret';
    document.getElementById('wordDisplayInner').appendChild(caret);
    return caret;
}

function scrollToWord(el) {
    const container = document.getElementById('wordDisplayInner');
    const wrapper = document.getElementById('wordDisplayWrapper');
    
    if (el.offsetTop > wrapper.offsetHeight / 2) {
        gsap.to(container, {
            y: -(el.offsetTop - 40),
            duration: 0.4,
            ease: 'power2.out'
        });
    }
}

// ──────────────────────────────────────
// HELPERS
// ──────────────────────────────────────

function setupEventListeners() {
    const input = document.getElementById('hiddenInput');
    if (input) {
        input.addEventListener('input', handleInput);
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                restartTest();
            }
            input.focus();
        });
    }
    
    document.getElementById('wordDisplayWrapper')?.addEventListener('click', () => {
        input.focus();
    });
}

function restartTest() {
    state = {
        ...state,
        currentIndex: 0,
        currentInput: '',
        startTime: null,
        timer: CONFIG.DEFAULT_TIME,
        isActive: false,
        isFinished: false,
        stats: { ...state.stats, wpm: 0, streak: 0 }
    };
    initApp();
    gsap.to('.notebook', { x: 0, rotation: 0, duration: 0.5 });
}

function endTest() {
    state.isFinished = true;
    state.isActive = false;
    // Show results overlay logic...
}

function loadProgress() {
    const saved = localStorage.getItem('typejaldi_stats');
    if (saved) state.user = JSON.parse(saved);
}

function updateUI() {
    const timerEl = document.getElementById('timerDisplay');
    if (timerEl) timerEl.innerText = state.timer;
}
