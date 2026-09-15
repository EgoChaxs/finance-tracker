const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const accessKey = document.getElementById("accessKey").value;
    const submitButton = loginForm.querySelector("button");

    loginError.textContent = "";
    submitButton.disabled = true;

    try {
        const response = await fetch("/auth/login", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "same-origin",

            body: JSON.stringify({
                name: name,
                access_key: accessKey
            })
        });

        const data = await response.json();

        if (!response.ok) {
            loginError.textContent =
                data.message || "Authentication failed.";

            return;
        }

        window.location.href = "/";

    } catch (error) {
        loginError.textContent =
            "Unable to connect to the server.";

    } finally {
        submitButton.disabled = false;
    }
});