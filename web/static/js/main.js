/*
DELIBERATELY VULNERABLE JAVASCRIPT - FOR EDUCATIONAL PURPOSES ONLY

This file demonstrates various client-side vulnerabilities.
*/

// CWE-79: Potential DOM-based XSS
// CWE-116: Improper encoding or escaping of output

console.log("⚠️ VULNERABLE APPLICATION LOADED ⚠️");
console.log("This application contains intentional security vulnerabilities.");
console.log("For educational purposes only - DO NOT use in production!");

// Initialize application
document.addEventListener('DOMContentLoaded', function() {

    // CWE-209: Information exposure through console logs
    console.log("User session token:", getCookie('session_token'));

    // Add event listeners
    setupFormHandlers();
    checkForMessages();

    // CWE-311: Missing encryption of sensitive data
    // Store sensitive data in localStorage (insecure)
    if (window.location.pathname === '/todos') {
        localStorage.setItem('lastVisit', new Date().toISOString());
    }
});

// Get cookie value
function getCookie(name) {
    // CWE-614: Cookies accessible via JavaScript (HttpOnly not set)
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Set cookie
function setCookie(name, value, days) {
    // CWE-614: Insecure cookie without Secure flag
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    // VULNERABILITY: No Secure or HttpOnly flags
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// Form handlers
function setupFormHandlers() {
    // Auto-save form data (insecure)
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // CWE-922: Insecure storage of sensitive information
        form.addEventListener('input', function(e) {
            if (e.target.type === 'password') {
                // VULNERABILITY: Storing password in localStorage
                localStorage.setItem('lastPassword', e.target.value);
            }
        });
    });
}

// Check for URL parameters
function checkForMessages() {
    const urlParams = new URLSearchParams(window.location.search);

    // CWE-79: DOM-based XSS - unsanitized parameter rendered to page
    const message = urlParams.get('message');
    if (message) {
        // VULNERABILITY: innerHTML with unsanitized user input
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message-box';
        messageDiv.innerHTML = message;  // XSS!
        document.body.insertBefore(messageDiv, document.body.firstChild);
    }

    // CWE-601: URL Redirection to Untrusted Site
    const redirect = urlParams.get('redirect');
    if (redirect) {
        // VULNERABILITY: Open redirect
        setTimeout(() => {
            window.location.href = redirect;  // No validation!
        }, 2000);
    }
}

// Fetch data from API (insecure)
function fetchTodoData(todoId) {
    // CWE-319: Cleartext transmission of sensitive information
    // CWE-352: No CSRF protection on API calls

    return fetch(`/api/todo/${todoId}`, {
        method: 'GET',
        // VULNERABILITY: No authentication headers
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // CWE-209: Exposing sensitive data in console
        console.log("Todo data:", data);
        return data;
    })
    .catch(error => {
        // VULNERABILITY: Exposing error details
        console.error("Error fetching todo:", error);
        alert("Error: " + error.message);
    });
}

// Create todo via API (vulnerable)
function createTodoAPI(title, description) {
    // CWE-352: No CSRF token
    const data = {
        user_id: 1,  // CWE-639: Hardcoded user ID
        title: title,
        description: description
    };

    return fetch('/api/todo/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // VULNERABILITY: No authentication or CSRF protection
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .catch(error => {
        console.error("Error creating todo:", error);
    });
}

// Search functionality (vulnerable to injection)
function searchTodos(query) {
    // CWE-79: XSS via unsanitized search query
    // Build URL without encoding
    const url = `/search?q=${query}`;  // Should be encodeURIComponent(query)
    window.location.href = url;
}

// Eval user input (extremely dangerous)
function executeUserScript(code) {
    // CWE-94: Code Injection
    // VULNERABILITY: eval() with user input
    try {
        eval(code);  // NEVER do this!
    } catch(e) {
        console.error("Script error:", e);
    }
}

// Download file (path traversal via client)
function downloadFile(filename) {
    // CWE-22: Path traversal possible
    // No validation of filename
    window.location.href = `/file/${filename}`;
}

// Admin command execution
function executeAdminCommand(command) {
    // CWE-78: OS Command Injection (client-side)
    const formData = new FormData();
    formData.append('command', command);

    return fetch('/admin/execute', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // VULNERABILITY: innerHTML with unsanitized output
        const outputDiv = document.getElementById('commandOutput');
        if (outputDiv) {
            outputDiv.innerHTML = '<pre>' + data.output + '</pre>';
        }
        return data;
    });
}

// SSRF demo function
function fetchExternalUrl(url) {
    // CWE-918: SSRF via user-controlled URL
    const formData = new FormData();
    formData.append('url', url);

    return fetch('/fetch-url', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("Fetched content:", data.content);
        return data;
    });
}

// XML import (XXE vulnerability)
function importXML(xmlString) {
    // CWE-611: XXE injection
    const formData = new FormData();
    formData.append('xml', xmlString);

    return fetch('/import-xml', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("XML import result:", data);
        return data;
    });
}

// Insecure random token generation
function generateInsecureToken() {
    // CWE-330: Use of insufficiently random values
    // VULNERABILITY: Math.random() is not cryptographically secure
    return Math.random().toString(36).substring(2, 15);
}

// Cross-site request helper (CSRF)
function makeUnauthenticatedRequest(url, data) {
    // CWE-352: CSRF attack helper
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;

    for (const key in data) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}

// Expose functions for educational purposes
window.vulnerableFunctions = {
    getCookie,
    setCookie,
    fetchTodoData,
    createTodoAPI,
    searchTodos,
    executeUserScript,  // Extremely dangerous!
    downloadFile,
    executeAdminCommand,
    fetchExternalUrl,
    importXML,
    generateInsecureToken,
    makeUnauthenticatedRequest
};

// Log available vulnerable functions
console.log("Available vulnerable functions:", Object.keys(window.vulnerableFunctions));
console.log("Access via: window.vulnerableFunctions.functionName()");
