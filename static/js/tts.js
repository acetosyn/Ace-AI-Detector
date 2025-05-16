window.addEventListener('DOMContentLoaded', () => {
    const synth = window.speechSynthesis;

    synth.onvoiceschanged = () => {
        setTimeout(() => {
            const aiResult = document.querySelector('.result-item p:nth-of-type(1)');
            const aiPercent = document.querySelector('.result-item p:nth-of-type(3)');

            if (!aiResult || !aiPercent) return;

            const resultContentRaw = aiResult.textContent.trim();
            const resultContent = resultContentRaw.toUpperCase();
            const percentContent = aiPercent.textContent.trim();

            let resultText = '';
            let extraMessage = '';

            if (resultContent.includes("AI GENERATED")) {
                resultText = `The text appears to be AI generated, with a confidence score of ${percentContent}.`;
                extraMessage = "This suggests the content was likely produced by an artificial intelligence model.";
            } else if (resultContent.includes("PASSES AS HUMAN") || resultContent.includes("HUMAN WRITTEN")) {
                resultText = `The text passes as human, with a confidence score of ${percentContent}.`;
                extraMessage = "This indicates the content was likely written by a human being.";
            } else {
                console.warn("Text classification not recognized:", resultContentRaw);
                return;
            }

            const fullMessage = `${resultText} ${extraMessage}`;
            const utterance = new SpeechSynthesisUtterance(fullMessage);

            const voices = synth.getVoices();
            const preferredVoice = voices.find(voice =>
                voice.name.toLowerCase().includes("female") ||
                voice.name.toLowerCase().includes("samantha") ||
                voice.name.toLowerCase().includes("google") ||
                voice.name.toLowerCase().includes("zira")
            );

            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            utterance.rate = 1;
            utterance.pitch = 1;
            synth.speak(utterance);
        }, 1000);
    };
});
