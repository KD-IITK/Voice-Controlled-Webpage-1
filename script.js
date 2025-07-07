document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prompt-form');
    const promptInput = document.getElementById('prompt-input');
    const responseContainer = document.getElementById('response-container');

    form.addEventListener('submit', async (event) => {
        // Prevent the form from reloading the page
        event.preventDefault();

        const prompt = promptInput.value;
        if (!prompt) return;

        // Display a loading message while waiting for the server
        responseContainer.textContent = 'Processing your request...';
        responseContainer.classList.add('loading');

        try {
            // Send the user's prompt to the /chat API endpoint
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt: prompt }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
            }

            // Get the JSON data from the successful response
            const data = await response.json();

            // Display the formatted JSON response in the container
            // JSON.stringify(data, null, 2) makes the JSON output readable ("pretty-print")
            responseContainer.textContent = JSON.stringify(data, null, 2);
            responseContainer.classList.remove('loading');

        } catch (error) {
            console.error('Error:', error);
            responseContainer.textContent = `An error occurred: ${error.message}`;
            responseContainer.classList.remove('loading');
        } finally {
            // Clear the input field for the next prompt
            promptInput.value = '';
        }
    });
});
