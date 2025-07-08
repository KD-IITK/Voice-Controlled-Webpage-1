class VoiceKioskApp {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkMicrophoneSupport();
    }

    initializeElements() {
        this.form = document.getElementById('prompt-form');
        this.promptInput = document.getElementById('prompt-input');
        this.voiceBtn = document.getElementById('voice-btn');
        this.responseContainer = document.getElementById('response-container');
        this.statusDiv = document.getElementById('status');
    }

    setupEventListeners() {
        // Text form submission
        this.form.addEventListener('submit', (e) => this.handleTextSubmit(e));
        
        // Voice button click
        this.voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
    }

    checkMicrophoneSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.statusDiv.textContent = 'Voice input not supported in this browser';
            this.voiceBtn.disabled = true;
        }
    }

    async toggleVoiceRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.voiceBtn.textContent = '🛑 Stop';
            this.voiceBtn.classList.add('recording');
            this.statusDiv.textContent = 'Recording... Click stop when finished';
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.statusDiv.textContent = 'Error: Could not access microphone';
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.voiceBtn.textContent = '🎤 Voice';
            this.voiceBtn.classList.remove('recording');
            this.statusDiv.textContent = 'Processing audio...';
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    async processRecording() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Send audio to Flask backend
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        
        try {
            const response = await fetch('/voice-to-text', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Put transcribed text in input field
                this.promptInput.value = data.text;
                this.statusDiv.textContent = `Transcribed: "${data.text}"`;
                
                // Automatically submit the transcribed text
                this.handleChatRequest(data.text);
            } else {
                this.statusDiv.textContent = `Error: ${data.error}`;
            }
            
        } catch (error) {
            console.error('Error processing audio:', error);
            this.statusDiv.textContent = `Error processing audio: ${error.message}`;
        }
    }

    async handleTextSubmit(event) {
        event.preventDefault();
        const prompt = this.promptInput.value;
        if (!prompt) return;
        
        await this.handleChatRequest(prompt);
    }

    async handleChatRequest(prompt) {
        this.responseContainer.textContent = 'Processing your request...';
        this.responseContainer.classList.add('loading');
        
        try {
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

            const data = await response.json();
            this.responseContainer.textContent = JSON.stringify(data, null, 2);
            this.responseContainer.classList.remove('loading');

        } catch (error) {
            console.error('Error:', error);
            this.responseContainer.textContent = `An error occurred: ${error.message}`;
            this.responseContainer.classList.remove('loading');
        } finally {
            this.promptInput.value = '';
            this.statusDiv.textContent = '';
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceKioskApp();
});
