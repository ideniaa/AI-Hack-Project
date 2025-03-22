document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatOutput = document.getElementById("chat-output");

    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        let userMessage = chatInput.value;

        let response = await fetch("/chatbot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userMessage })
        });

        let data = await response.json();
        chatOutput.innerHTML += `<p><strong>You:</strong> ${userMessage}</p>`;
        chatOutput.innerHTML += `<p><strong>Bot:</strong> ${data.response}</p>`;
        
        chatInput.value = "";
    });
});
