let currentLabel;
let round = 1;
let currentScore = 0; // Initialize score to 0
const synth = window.speechSynthesis;
const OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"; // Add your OpenAI API key here

function startGame() {
    currentScore = 0; // Reset score at the start
    document.getElementById('startButton').style.display = 'none'; // Hide the Play Game button
    document.getElementById('gameContainer').style.display = 'block'; // Show the game container
    loadRandomContent(); // Start loading content
}

// Function to fetch text optimized for TTS from OpenAI
async function fetchEnhancedText(text) {
    try {
        const response = await fetch("https://api.openai.com/v1/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${OPENAI_API_KEY}`,
            },
            body: JSON.stringify({
                model: "text-davinci-003",
                prompt: `Read this in a natural female voice tone: ${text}`,
                max_tokens: 100,
            }),
        });
        const data = await response.json();
        return data.choices[0].text.trim();
    } catch (error) {
        console.error("Error fetching text from OpenAI:", error);
        return text; // Fallback to original text if API call fails
    }
}

async function loadRandomContent() {
    stopSpeaking(); // Stop any ongoing speech before loading new content
    try {
        const response = await fetch(`/get_random_content?score=${currentScore}`);
        const data = await response.json();

        const contentElement = document.getElementById('gameContent');
        const instructionsElement = document.querySelector('.game-instructions');
        const feedbackMessage = document.getElementById('feedbackMessage');

        // Clear previous content and feedback
        contentElement.innerHTML = '';
        feedbackMessage.textContent = '';

        if (data.type === 'end') {
            displayEndGameOptions(data.score); // Display Play Again, End Game, and Analysis
            return;
        }

        // Apply slide-in animation
        contentElement.classList.add('slide-animation');
        setTimeout(() => contentElement.classList.remove('slide-animation'), 1500);

        if (data.type === 'text') {
            instructionsElement.textContent = "Can you guess if the text below is AI-generated or human-written?";
            const enhancedText = await fetchEnhancedText(data.content); // Get enhanced text from OpenAI
            contentElement.textContent = enhancedText;
            currentLabel = data.label;
            round = data.round;

            // Trigger TTS with the Web Speech API for client-side playback
            speakText(enhancedText, data.label);

        } else if (data.type === 'image') {
            instructionsElement.textContent = "Can you tell the difference between AI-generated images and real images?";
            const imgElement = document.createElement('img');
            imgElement.src = data.content;
            imgElement.alt = "Random Image";
            imgElement.width = 1000;
            imgElement.classList.add('slide-animation'); // Apply animation
            contentElement.appendChild(imgElement);
            currentLabel = data.label;
            round = data.round;
        }
    } catch (error) {
        console.error("Error fetching random content:", error);
    }
}

function speakText(text, label) {
    // Replace periods with a period followed by two spaces for a brief pause
    const processedText = text.replace(/\./g, '.  ');

    const voices = synth.getVoices();
    let selectedVoice;
    if (label === 1) {
        selectedVoice = voices.find(voice => voice.name.includes("Alex")) || voices[0];
    } else {
        selectedVoice = voices.find(voice => voice.name.includes("Samantha")) || voices.find(voice => voice.gender === "female") || voices[0];
    }

    const utterance = new SpeechSynthesisUtterance(processedText);
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

    if ((guess === 'ai' && currentLabel === 1) || (guess === 'human' && currentLabel === 0)) {
        feedbackMessage.textContent = "Correct! Well done!";
        feedbackMessage.style.color = "#5cb85c";
        currentScore++; // Increment score only on correct guess
    } else {
        feedbackMessage.textContent = "Oops! That was incorrect.";
        feedbackMessage.style.color = "#d9534f";
    }

    // Update score display in the scoreboard
    document.getElementById('score').textContent = currentScore;
    
    // Delay to show feedback before loading the next content
    setTimeout(loadRandomContent, 1500);
}

// Function to display end-game options with analysis
function displayEndGameOptions(score) {
    const feedbackMessage = document.getElementById('feedbackMessage');
    feedbackMessage.textContent = `Game Over! Your Score: ${score}`;
    feedbackMessage.style.color = "#333";

    const contentElement = document.getElementById('gameContent');
    contentElement.innerHTML = '';

    // Hide guess buttons and score display
    document.querySelector('.guess-buttons').style.display = 'none';
    document.querySelector('.scoreboard').style.display = 'none';

    // Analysis section
    const analysisSection = document.createElement('div');
    analysisSection.className = 'analysis-section';
    analysisSection.innerHTML = `<h3>Game Analysis</h3><p>You scored ${score} out of 10.</p>`;
    analysisSection.innerHTML += `<p>${score >= 7 ? "Excellent performance!" : score >= 4 ? "Good try!" : "Better luck next time!"}</p>`;
    contentElement.appendChild(analysisSection);

    // Play Again and End Game buttons container
    const endGameOptions = document.createElement('div');
    endGameOptions.className = 'end-game-options';

    // Play Again button
    const playAgainButton = document.createElement('button');
    playAgainButton.textContent = "Play Again";
    playAgainButton.className = 'play-again-button';
    playAgainButton.onclick = startGame;
    endGameOptions.appendChild(playAgainButton);

    // End Game button
    const endGameButton = document.createElement('button');
    endGameButton.textContent = "End Game";
    endGameButton.className = 'end-game-button';
    endGameButton.onclick = () => {
        window.location.href = '/plagiarism'; // Redirect to Plagiarism page
    };
    endGameOptions.appendChild(endGameButton);

    contentElement.appendChild(endGameOptions);
}

// Stop speaking when the page is unloaded (e.g., reloaded or closed)
window.onbeforeunload = stopSpeaking;

// Start game on clicking the start button
document.getElementById('startButton').addEventListener('click', startGame);
