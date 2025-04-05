let currentLabel;
let round = 1;
const synth = window.speechSynthesis;

function startGame() {
    document.getElementById('startButton').style.display = 'none';
    document.getElementById('gameContainer').style.display = 'block';
    loadRandomContent();
}

async function loadRandomContent() {
    stopSpeaking(); // Stop any ongoing speech before loading new content
    
    try {
        const response = await fetch('/get_random_content');
        const data = await response.json();

        const contentElement = document.getElementById('gameContent');
        const instructionsElement = document.querySelector('.game-instructions');
        const feedbackMessage = document.getElementById('feedbackMessage');

        contentElement.innerHTML = '';
        feedbackMessage.textContent = '';

        if (data.type === 'text') {
            instructionsElement.textContent = "Can you guess if the text below is AI-generated or human-written?";
            contentElement.textContent = data.content;
            currentLabel = data.label;
            round = data.round;

            // Trigger TTS with the Web Speech API for client-side playback
            speakText(data.content, data.label);
        } else if (data.type === 'image') {
            instructionsElement.textContent = "Can you tell the difference between AI-generated images and real images?";
            const imgElement = document.createElement('img');
            imgElement.src = data.content;
            imgElement.alt = "Random Image";
            imgElement.width = 500;
            contentElement.appendChild(imgElement);
            currentLabel = data.label;
            round = data.round;
        } else if (data.type === 'end') {
            feedbackMessage.textContent = `${data.content} Your Score: ${data.score}`;
            document.getElementById('gameContent').innerHTML = `<button onclick="startGame()">Play Again</button>`;
            return;
        }
    } catch (error) {
        console.error("Error fetching random content:", error);
    }
}

function speakText(text, label) {
    const voices = synth.getVoices();
    let selectedVoice;
    if (label === 1) {
        selectedVoice = voices.find(voice => voice.name.includes("Alex")) || voices[0];
    } else {
        selectedVoice = voices.find(voice => voice.name.includes("Samantha")) || voices.find(voice => voice.gender === "female") || voices[0];
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = selectedVoice;
    synth.speak(utterance);
}

function stopSpeaking() {
    if (synth.speaking) {
        synth.cancel(); // Stop any ongoing speech immediately
    }
}

function submitGuess(guess) {
    stopSpeaking(); // Stop the voice when a guess is submitted

    const feedbackMessage = document.getElementById('feedbackMessage');
    const scoreElement = document.getElementById('score');
    let score = parseInt(scoreElement.textContent);

    if ((guess === 'ai' && currentLabel === 1) || (guess === 'human' && currentLabel === 0)) {
        feedbackMessage.textContent = "Correct! Well done!";
        feedbackMessage.style.color = "#5cb85c";
        score++;
    } else {
        feedbackMessage.textContent = "Oops! That was incorrect.";
        feedbackMessage.style.color = "#d9534f";
    }

    scoreElement.textContent = score;
    setTimeout(loadRandomContent, 1500);
}

// Stop speaking when the page is unloaded (e.g., reloaded or closed)
window.onbeforeunload = stopSpeaking;

document.getElementById('startButton').addEventListener('click', startGame);
