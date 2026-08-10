document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("form[action$='/analyze'] button");
    buttons.forEach(button => {
        button.addEventListener("click", () => {
            button.disabled = true;
            button.innerHTML = "🤖 AI Agents Running...";
        });
    });
});
