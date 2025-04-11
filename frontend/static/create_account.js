document.querySelector('form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const username = document.querySelector('input[type="text"]').value;
    const email = document.querySelector('input[name="email"]').value;
    const password = document.querySelector('input[type="password"]').value;
    const confirmPassword = document.querySelector('input[type="confirm_password"]').value;

    const response = await fetch('/create_account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ 
            username,
            email, 
            password,
            confirmPassword
        })
    });

    if (response.redirected) {
        window.location.href = response.url;
    } else {
        const result = await response.json();
        if (result.error) {
            alert(result.error);
        } else {
            alert(result.success);
        }
    }
});