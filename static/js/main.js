// Redirect to AI_game page
document.getElementById("playGameButton").addEventListener("click", function () {
    window.location.href = "/ai_game";
});

// Automatically hide flash messages after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach((message) => {
        message.style.display = 'none';
    });
}, 5000);

// Maintain plagiarism page view on refresh
document.addEventListener("DOMContentLoaded", function () {
    if (sessionStorage.getItem("plagiarismPageShown") === "true") {
        document.getElementById("introSection").style.display = "none";
        document.getElementById("plagiarismPage").style.display = "block";
    }
});