// Backend URL (change to your deployed URL later)
const BACKEND_URL = 'https://campus-print-2-0.onrender.com';

function toggleForms() {
    document.getElementById('login-form').classList.toggle('hidden');
    document.getElementById('signup-form').classList.toggle('hidden');
    document.getElementById('message').innerText = "";
}

function submitForm(action) {
    const userField = action === 'login' ? 'login-user' : 'signup-user';
    const passField = action === 'login' ? 'login-pass' : 'signup-pass';

    const username = document.getElementById(userField).value;
    const password = document.getElementById(passField).value;
    const messageBox = document.getElementById('message');

    if (!username || !password) {
        messageBox.innerText = "Please fill in all fields.";
        messageBox.style.color = "red";
        return;
    }

    messageBox.innerText = "Processing...";
    messageBox.style.color = "black";

    // Send request to Python backend
    fetch(`${BACKEND_URL}/api/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            // Handle HTTP errors (401, 400, etc.)
            throw new Error(data.detail || "Authentication failed");
        }
        return data;
    })
    .then(data => {
        // Successful login or signup returns { access_token, token_type }
        if (data.access_token) {
            messageBox.style.color = "green";
            messageBox.innerText = action === 'login' ? "Login successful! Redirecting..." : "Account created! Please login.";
            
            if (action === 'signup') {
                // Clear signup form and switch to login view after 1.5s
                document.getElementById('signup-user').value = '';
                document.getElementById('signup-pass').value = '';
                setTimeout(() => {
                    toggleForms(); // switch to login form
                    messageBox.innerText = ""; // clear message
                }, 1500);
            } else {
                // Login success: store token and username
                localStorage.setItem('campusUser', username);
                localStorage.setItem('token', data.access_token);
                // Redirect to main page
                window.location.href = 'main.html';
            }
        } else {
            // Unexpected response (should not happen with proper backend)
            messageBox.style.color = "red";
            messageBox.innerText = "Unexpected server response.";
        }
    })
    .catch(error => {
        messageBox.style.color = "red";
        messageBox.innerText = error.message || "Error connecting to server.";
        console.error('Error:', error);
    });
}