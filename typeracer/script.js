// Game state variables
let currentSentence = "The quick brown fox jumps over the lazy dog.";
let currentPosition = 0;
let startTime = null;
let gameCompleted = false;
let correctChars = 0;

// Array of sentences for randomization
const sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "How vexingly quick daft zebras jump!",
    "Bright vixens jump; dozy fowl quack.",
    "Sphinx of black quartz, judge my vow.",
    "Two driven jocks help fax my big quiz.",
    "Quick zephyrs blow, vexing daft Jim.",
    "Waltz, bad nymph, for quick jigs vex.",
    "Glib jocks quiz nymph to vex dwarf.",
    "Jackdaws love my big sphinx of quartz."
];

// DOM elements
const sentenceElement = document.getElementById('sentence');
const typingInput = document.getElementById('typing-input');
const carElement = document.getElementById('car');
const wpmElement = document.getElementById('wpm');
const progressElement = document.getElementById('progress');
const completionMessage = document.getElementById('completion-message');

// Initialize the game
function initGame() {
    // Choose random sentence
    currentSentence = sentences[Math.floor(Math.random() * sentences.length)];
    
    // Reset game state
    currentPosition = 0;
    startTime = null;
    gameCompleted = false;
    correctChars = 0;
    
    // Update UI
    setupSentenceHighlighting();
    typingInput.value = '';
    typingInput.disabled = false;
    carElement.style.left = '0%';
    wpmElement.textContent = '0';
    progressElement.textContent = '0%';
    completionMessage.classList.add('hidden');
    
    // Focus input
    typingInput.focus();
}

// Setup sentence with individual character spans for highlighting
function setupSentenceHighlighting() {
    sentenceElement.innerHTML = '';
    for (let i = 0; i < currentSentence.length; i++) {
        const span = document.createElement('span');
        span.className = 'char';
        span.textContent = currentSentence[i];
        if (i === 0) {
            span.classList.add('current');
        }
        sentenceElement.appendChild(span);
    }
}

// Handle typing input
typingInput.addEventListener('input', function(e) {
    if (gameCompleted) return;
    
    // Start timer on first keystroke
    if (startTime === null) {
        startTime = Date.now();
    }
    
    const typedText = e.target.value;
    const chars = sentenceElement.querySelectorAll('.char');
    
    // Reset all character classes
    chars.forEach((char, index) => {
        char.className = 'char';
    });
    
    // Update character highlighting
    for (let i = 0; i < Math.min(typedText.length, currentSentence.length); i++) {
        if (typedText[i] === currentSentence[i]) {
            chars[i].classList.add('correct');
            correctChars = i + 1;
        } else {
            chars[i].classList.add('incorrect');
            correctChars = i;
            break;
        }
    }
    
    // Highlight current character
    if (typedText.length < currentSentence.length) {
        chars[typedText.length].classList.add('current');
    }
    
    // Update car position based on correct characters
    const progress = (correctChars / currentSentence.length) * 100;
    carElement.style.left = `${Math.min(progress, 95)}%`;
    
    // Update progress display
    progressElement.textContent = `${Math.round(progress)}%`;
    
    // Update WPM
    updateWPM();
    
    // Check if game is completed
    if (typedText === currentSentence) {
        completeGame();
    }
});

// Calculate and update WPM
function updateWPM() {
    if (startTime === null) return;
    
    const currentTime = Date.now();
    const timeElapsed = (currentTime - startTime) / 1000 / 60; // in minutes
    const wordsTyped = correctChars / 5; // Standard: 5 characters = 1 word
    const wpm = Math.round(wordsTyped / timeElapsed);
    
    wpmElement.textContent = isFinite(wpm) ? wpm : 0;
}

// Complete the game
function completeGame() {
    gameCompleted = true;
    typingInput.disabled = true;
    
    // Move car to finish line
    carElement.style.left = '95%';
    
    // Update final WPM display
    const finalWpmElement = document.getElementById('final-wpm');
    if (finalWpmElement) {
        finalWpmElement.textContent = wpmElement.textContent;
    }
    
    // Show completion message
    completionMessage.classList.remove('hidden');
    
    // Add confetti effect
    createConfetti();
}

// Create confetti animation
function createConfetti() {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd'];
    
    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
            confetti.style.zIndex = '1000';
            confetti.style.borderRadius = '50%';
            confetti.style.pointerEvents = 'none';
            
            document.body.appendChild(confetti);
            
            // Animate confetti falling
            const animation = confetti.animate([
                { transform: 'translateY(0px) rotate(0deg)', opacity: 1 },
                { transform: 'translateY(' + (window.innerHeight + 100) + 'px) rotate(720deg)', opacity: 0 }
            ], {
                duration: 3000,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            });
            
            animation.onfinish = () => {
                confetti.remove();
            };
        }, i * 50);
    }
}

// Reset game function
function resetGame() {
    initGame();
}

// Handle keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Focus input when any key is pressed (except special keys)
    if (!e.ctrlKey && !e.altKey && !e.metaKey && e.key.length === 1) {
        if (document.activeElement !== typingInput) {
            typingInput.focus();
        }
    }
    
    // Reset game with Escape key
    if (e.key === 'Escape') {
        resetGame();
    }
});

// Prevent input from losing focus
typingInput.addEventListener('blur', function() {
    if (!gameCompleted) {
        setTimeout(() => typingInput.focus(), 10);
    }
});

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', function() {
    initGame();
}); 