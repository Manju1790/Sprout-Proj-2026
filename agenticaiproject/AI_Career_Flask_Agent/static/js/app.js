document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("form[action$='/analyze']");
    forms.forEach(form => {
        const button = form.querySelector("button");
        if (!button) return;

        button.addEventListener("click", async event => {
            event.preventDefault();
            button.disabled = true;
            button.innerHTML = "🤖 AI Agents Running...";

            try {
                await fetch(form.action, {
                    method: "POST",
                    credentials: "same-origin",
                });
            } catch (error) {
                console.error("Analysis request failed:", error);
            }

            window.location.href = "/results";
        });
    });
});
