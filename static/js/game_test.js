let currentLabel;
let round = 1;
let currentScore = 0; // Initialize score to 0

function startGame() {
    currentScore = 0; // Reset score at the start
    document.getElementById('startButton').style.display = 'none'; // Hide the Play Game button
    document.getElementById('gameContainer').style.display = 'block'; // Show the game container
    loadRandomContent(); // Start loading content
}
async function loadRandomContent() {
    try {
        const response = await fetch(`/get_random_content?score=${currentScore}`);
        const data = await response.json();

        const contentElement = document.getElementById('gameContent');
        const instructionsElement = document.querySelector('.game-instructions');
        const feedbackMessage = document.getElementById('feedbackMessage');

        contentElement.innerHTML = '';
        feedbackMessage.textContent = '';

        if (data.type === 'end') {
            displayEndGameOptions(data.score);
            return;
        }

        if (data.type === 'text') {
            instructionsElement.textContent = "Can you guess if the text below is AI-generated or human-written?";
            contentElement.textContent = data.content;
            currentLabel = data.label;
            round = data.round;

            // Fetch and play enhanced narration from the backend
            fetchAndPlayNarration(data.content);
        } else if (data.type === 'image') {
            instructionsElement.textContent = "Can you tell the difference between AI-generated images and real images?";
            const imgElement = document.createElement('img');
            imgElement.src = data.content;
            imgElement.alt = "Random Image";
            imgElement.width = 1000;
            imgElement.classList.add('slide-animation');
            contentElement.appendChild(imgElement);
            currentLabel = data.label;
            round = data.round;
        }
    } catch (error) {
        console.error("Error fetching random content:", error);
    }
}

async function fetchAndPlayNarration(text) {
    try {
        const response = await fetch('/generate_and_narrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await response.json();
        const audio = new Audio(data.audio_url);
        audio.play();
    } catch (error) {
        console.error("Error fetching narration:", error);
    }
}


function submitGuess(guess) {
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

// Start game on clicking the start button
document.getElementById('startButton').addEventListener('click', startGame);
