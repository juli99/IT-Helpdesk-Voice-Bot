document.addEventListener('DOMContentLoaded', () => {
    const orbButton            = document.getElementById('orbButton');
    const orbStatus            = document.getElementById('orbStatus');
    const lottieContainerPink  = document.getElementById('lottieContainerPink');
    const lottieContainerGreen = document.getElementById('lottieContainerGreen');
    const chatBox              = document.getElementById('chatBox');
    const themeToggle          = document.getElementById('themeToggle');
    const voiceToggle          = document.getElementById('voiceToggle');
    const voiceIcon            = document.getElementById('voiceIcon');
    const resetButton          = document.getElementById('resetButton');
    const humanButton          = document.getElementById('humanButton');

    let currentVoiceGender = 'male';
    let currentState       = 'ready';
    let isFirstClick       = true;
    let mediaRecorder;
    let audioChunks        = [];
    let recordingStartTime = 0;

    voiceIcon.src = '/frontend/male_icon.png';

    // ── Lottie animations ────────────────────────────────────────
    let animationPink = lottie.loadAnimation({
        container: lottieContainerPink,
        renderer: 'svg', loop: true, autoplay: false,
        path: '/frontend/wave_pink.json'
    });

    let animationGreen = lottie.loadAnimation({
        container: lottieContainerGreen,
        renderer: 'svg', loop: true, autoplay: false,
        path: '/frontend/wave_green.json'
    });

    // ── Orb state machine ────────────────────────────────────────
    function setOrbState(state) {
        currentState = state;
        animationPink.stop();
        animationGreen.stop();
        lottieContainerPink.style.opacity  = 0;
        lottieContainerGreen.style.opacity = 0;

        if (state === 'ready') {
            orbButton.classList.remove('active');
            orbStatus.innerText = "Push to Talk";
        } else if (state === 'listening') {
            orbButton.classList.add('active');
            orbStatus.innerText = "Listening";
            lottieContainerGreen.style.opacity = 1;
            animationGreen.goToAndPlay(0, true);
        } else if (state === 'processing') {
            orbStatus.innerText = "Thinking...";
        } else if (state === 'speaking') {
            orbButton.classList.add('active');
            orbStatus.innerText = "Speaking";
            lottieContainerPink.style.opacity = 1;
            animationPink.goToAndPlay(0, true);
        }
    }

    // ── Chat rendering ───────────────────────────────────────────
    function appendMessage(text, className) {
        const msg = document.createElement('div');
        msg.classList.add('message', className);
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
        typeWriterElement(text, msg);
    }

    function typeWriterElement(text, element, speed = 28) {
        element.textContent = "";
        let i = 0;
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i++);
                chatBox.scrollTop = chatBox.scrollHeight;
                setTimeout(type, speed);
            }
        }
        type();
    }

    // ── TTS playback ─────────────────────────────────────────────
    async function playAudio(text) {
        try {
            const response = await fetch('/speak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice_id: currentVoiceGender })
            });
            const data = await response.json();
            if (data.audio) {
                const audio = new Audio("data:audio/mpeg;base64," + data.audio);
                setOrbState('speaking');
                audio.play().catch(e => { console.error(e); setOrbState('ready'); });
                audio.onended = () => setOrbState('ready');
            } else {
                setOrbState('ready');
            }
        } catch (e) {
            console.error(e);
            setOrbState('ready');
        }
    }

    // ── Main recording handler ───────────────────────────────────
    orbButton.addEventListener('mousedown', async () => {
        // Unlock AudioContext on first interaction (iOS / strict browsers)
        if (window.AudioContext) {
            const ctx = new AudioContext();
            if (ctx.state === 'suspended') await ctx.resume();
        }

        // First click: show welcome message
        if (isFirstClick) {
            isFirstClick = false;
            chatBox.classList.add('visible');
            const welcome = "Hello, I'm Alex, your IT support assistant. How can I help you today?";
            appendMessage("Bot: " + welcome, 'bot-message');
            await playAudio(welcome);
            return;
        }

        if (currentState !== 'ready') return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks   = [];
            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

            mediaRecorder.onstop = async () => {
                setOrbState('processing');

                // Pick the best supported mime type
                let mime = 'audio/webm';
                if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                    mime = 'audio/webm;codecs=opus';
                } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                    mime = 'audio/ogg;codecs=opus';
                }

                const blob     = new Blob(audioChunks, { type: mime });
                const duration = Date.now() - recordingStartTime;
                console.log(`[Audio] ${blob.size} bytes, ${duration}ms, ${mime}`);

                // Reject recordings that are too short or empty
                if (duration < 500 || blob.size < 3000) {
                    appendMessage("Bot: I didn't catch that — please hold the button while you speak.", 'bot-message');
                    setOrbState('ready');
                    return;
                }

                const ext      = mime.includes('ogg') ? 'ogg' : 'webm';
                const formData = new FormData();
                formData.append('file', blob, `recording.${ext}`);
                formData.append('voice_id', currentVoiceGender);

                try {
                    const res  = await fetch('/process', { method: 'POST', body: formData });
                    const data = await res.json();

                    if (data.error === 'no_audio') {
                        appendMessage("Bot: I didn't catch that — please try again.", 'bot-message');
                        setOrbState('ready');
                        return;
                    }

                    if (data.error) {
                        console.error("Backend error:", data.error);
                        setOrbState('ready');
                        return;
                    }

                    // Show transcript and bot response
                    if (data.corrected_transcript) {
                        appendMessage("You: " + data.corrected_transcript, 'user-message');
                    }
                    if (data.bot_message) {
                        appendMessage("Bot: " + data.bot_message, 'bot-message');
                        await playAudio(data.bot_message);
                    }

                    // Lock UI and show ticket on escalate / close
                    if (data.action === 'escalate') {
                        lockSession('Escalated');
                        if (data.ticket) appendMessage("System: Ticket created successfully.", 'system-message');
                    } else if (data.action === 'close') {
                        lockSession('Session closed');
                        if (data.ticket) appendMessage("System: Ticket created successfully.", 'system-message');
                    }

                } catch (err) {
                    console.error("Pipeline error:", err);
                    setOrbState('ready');
                }
            };

            mediaRecorder.start(100);
            recordingStartTime = Date.now();
            setOrbState('listening');

        } catch (err) {
            console.error("Mic error:", err);
        }
    });

    orbButton.addEventListener('mouseup', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
    });

    // ── Session lock (escalate / close / live-agent transfer) ────
    function lockSession(buttonLabel) {
        orbButton.style.pointerEvents = 'none';
        orbButton.style.opacity       = '0.4';
        if (humanButton) {
            humanButton.disabled    = true;
            humanButton.textContent = buttonLabel;
        }
    }

    // ── Live Agent transfer ───────────────────────────────────────
    async function transferToHuman() {
        if (isFirstClick) {
            isFirstClick = false;
            chatBox.classList.add('visible');
        }
        appendMessage("You: Please connect me to a human representative.", 'user-message');
        const msg = "Connecting you to a human representative now. Please hold while I transfer your call.";
        appendMessage("Bot: " + msg, 'bot-message');
        await playAudio(msg);

        lockSession('Transfer in progress');
    }

    if (humanButton) {
        humanButton.addEventListener('click', transferToHuman);
    }

    // ── Theme toggle ──────────────────────────────────────────────
    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        themeToggle.innerText = isDark ? '🌙' : '🔅';
    });

    // ── Voice toggle ──────────────────────────────────────────────
    voiceToggle.addEventListener('click', () => {
        currentVoiceGender = currentVoiceGender === 'male' ? 'female' : 'male';
        voiceIcon.src = currentVoiceGender === 'male'
            ? '/frontend/male_icon.png'
            : '/frontend/female_icon.png';
    });

    // ── Reset ────────────────────────────────────────────────────
    resetButton.addEventListener('click', async () => {
        // Spin animation
        const img = resetButton.querySelector('img');
        img.classList.remove('reset-spin');
        void img.offsetWidth;
        img.classList.add('reset-spin');

        // Clear server-side conversation history
        try {
            await fetch('/reset', { method: 'POST' });
        } catch (e) {
            console.warn("Reset endpoint error:", e);
        }

        // Reset client state
        currentState = 'ready';
        isFirstClick = true;

        orbStatus.innerText = "Push to Talk";
        orbButton.classList.remove('active');
        orbButton.style.pointerEvents = '';
        orbButton.style.opacity       = '';

        chatBox.innerHTML = '';
        chatBox.classList.remove('visible');

        if (humanButton) {
            humanButton.disabled    = false;
            humanButton.textContent = 'Live Agent';
        }
    });
});
