document.addEventListener('DOMContentLoaded', () => {
    const orbButton = document.getElementById('orbButton');
    const orbStatus = document.getElementById('orbStatus');
    const lottieContainerPink = document.getElementById('lottieContainerPink');
    const lottieContainerGreen = document.getElementById('lottieContainerGreen');
    const chatBox = document.getElementById('chatBox');
    const themeToggle = document.getElementById('themeToggle');
    const voiceToggle = document.getElementById('voiceToggle');
    const voiceIcon = document.getElementById('voiceIcon');
    const resetButton = document.getElementById('resetButton');
    const humanButton = document.getElementById('humanButton');

    let currentVoiceGender = 'male';
    let currentState = 'ready';
    let isFirstClick = true;
    let mediaRecorder;
    let audioChunks = [];

    let currentStepIndex = 0;
    let inTroubleshoot = false;
    let currentIntent = 'other';
    let recordingStartTime = 0;

    // "working" excluded — it appears in "not working" and would false-positive.
    const POSITIVE = /\b(yes|yeah|yep|yup|fixed|worked|resolved|it works|all good|good now|thank you|thanks|perfect|great|that worked|that fixed)\b/i;
    const NEGATIVE = /\b(no|nope|nah|not|still|same|didn'?t|doesn'?t|isn'?t|not working|not fixed|still broken|didn'?t work|doesn'?t work)\b/i;

    voiceIcon.src = '/frontend/male_icon.png';

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

    // ── Troubleshoot follow-up handler ───────────────────────────
    // Called when inTroubleshoot=true. Receives only the ASR transcript
    // (no classification/routing), so state can never be corrupted by the pipeline.
    async function handleTroubleshootResponse(transcript) {
        if (!transcript) {
            appendMessage("Bot: I didn't catch that — could you say yes or no?", 'bot-message');
            setOrbState('ready');
            return;
        }

        appendMessage("You: " + transcript, 'user-message');
        const text = transcript.toLowerCase();

        if (POSITIVE.test(text)) {
            // User confirmed resolution
            inTroubleshoot = false;
            currentStepIndex = 0;
            const fd = new FormData();
            fd.append('voice_id', currentVoiceGender);
            try {
                const res = await fetch('/close', { method: 'POST', body: fd });
                const closeData = await res.json();
                if (closeData.bot_message) {
                    appendMessage("Bot: " + closeData.bot_message, 'bot-message');
                    await playAudio(closeData.bot_message);
                }
                if (closeData.ticket) {
                    console.log("Ticket generated on close:", closeData.ticket);
                    appendMessage("System: Ticket created successfully.", 'system-message');
                }
            } catch (e) {
                console.error("Close call failed:", e);
                setOrbState('ready');
            }

        } else if (NEGATIVE.test(text)) {
            // User says it didn't work — get next step
            currentStepIndex++;
            const fd = new FormData();
            fd.append('intent', currentIntent);
            fd.append('step', currentStepIndex);
            fd.append('voice_id', currentVoiceGender);
            try {
                const res = await fetch('/step', { method: 'POST', body: fd });
                const stepData = await res.json();
                if (stepData.bot_message) {
                    appendMessage("Bot: " + stepData.bot_message, 'bot-message');
                    await playAudio(stepData.bot_message);
                }
                if (stepData.action === 'escalate') {
                    inTroubleshoot = false;
                    currentStepIndex = 0;
                    if (stepData.ticket) {
                        appendMessage("System: Ticket created successfully.", 'system-message');
                    }
                }
            } catch (e) {
                console.error("Step call failed:", e);
                setOrbState('ready');
            }

        } else {
            // Ambiguous — ask user to confirm clearly
            const clarify = "Just to confirm — did that step resolve your issue?";
            appendMessage("Bot: " + clarify, 'bot-message');
            await playAudio(clarify);
        }
    }

    // ── Fresh issue handler (pipeline response) ──────────────────
    async function processBackendResponse(data) {
        if (data.error) {
            console.error("Backend Error:", data.error);
            setOrbState('ready');
            return;
        }

        if (data.corrected_transcript) {
            appendMessage("You: " + data.corrected_transcript, 'user-message');
        }

        if (data.intent) currentIntent = data.intent;

        if (data.bot_message) {
            appendMessage("Bot: " + data.bot_message, 'bot-message');
            await playAudio(data.bot_message);
        }

        if (data.action === 'troubleshoot') {
            inTroubleshoot = true;
        } else if (data.action === 'escalate' || data.action === 'close') {
            inTroubleshoot = false;
            currentStepIndex = 0;
            if (data.ticket) {
                console.log("Ticket generated:", data.ticket);
                appendMessage("System: Ticket created successfully.", 'system-message');
            }
        }
    }

    async function playAudio(text) {
        try {
            const response = await fetch('/speak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, voice_id: currentVoiceGender })
            });
            const data = await response.json();
            if (data.audio) {
                const audio = new Audio("data:audio/mpeg;base64," + data.audio);
                setOrbState('speaking');
                audio.play().catch(e => { console.error(e); setOrbState('ready'); });
                audio.onended = () => setOrbState('ready');
            } else { setOrbState('ready'); }
        } catch (e) { console.error(e); setOrbState('ready'); }
    }

    function setOrbState(state) {
        currentState = state;
        animationPink.stop(); animationGreen.stop();
        lottieContainerPink.style.opacity = 0; lottieContainerGreen.style.opacity = 0;
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

    function appendMessage(text, className) {
        const msg = document.createElement('div');
        msg.classList.add('message', className);
        chatBox.appendChild(msg);
        chatBox.scrollTop = chatBox.scrollHeight;
        typeWriterElement(text, msg);
    }

    function typeWriterElement(text, element, speed = 30) {
        element.textContent = "";
        let i = 0;
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                chatBox.scrollTop = chatBox.scrollHeight;
                setTimeout(type, speed);
            }
        }
        type();
    }

    orbButton.addEventListener('mousedown', async () => {
        if (window.AudioContext) {
            const ctx = new AudioContext();
            if (ctx.state === 'suspended') await ctx.resume();
        }

        if (isFirstClick) {
            isFirstClick = false;
            chatBox.classList.add('visible');
            const welcome = "Hello, I am your IT assistant. How can I help you today?";
            appendMessage("Bot: " + welcome, 'bot-message');
            await playAudio(welcome);
            return;
        }

        if (currentState === 'ready') {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

                mediaRecorder.onstop = async () => {
                    setOrbState('processing');

                    let supportedMime = 'audio/webm';
                    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                        supportedMime = 'audio/webm;codecs=opus';
                    } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                        supportedMime = 'audio/ogg;codecs=opus';
                    }

                    const audioBlob = new Blob(audioChunks, { type: supportedMime });
                    const recordingDuration = Date.now() - recordingStartTime;
                    console.log(`[Audio] ${audioBlob.size} bytes, ${recordingDuration}ms, ${supportedMime}`);

                    if (recordingDuration < 500 || audioBlob.size < 3000) {
                        appendMessage("Bot: I didn't catch that — please hold the button while you speak.", 'bot-message');
                        setOrbState('ready');
                        return;
                    }

                    const ext = supportedMime.includes('ogg') ? 'ogg' : 'webm';
                    const formData = new FormData();
                    formData.append('file', audioBlob, `recording.${ext}`);

                    if (inTroubleshoot) {
                        // Mid-troubleshoot: only need the transcript, skip classify+route.
                        try {
                            const res = await fetch('/asr', { method: 'POST', body: formData });
                            const asrData = await res.json();
                            await handleTroubleshootResponse(asrData.transcript || '');
                        } catch (err) {
                            console.error("ASR error:", err);
                            setOrbState('ready');
                        }
                    } else {
                        // Fresh issue: run the full pipeline.
                        formData.append('step', currentStepIndex);
                        formData.append('resolved', false);
                        formData.append('voice_id', currentVoiceGender);
                        try {
                            const res = await fetch('/process', { method: 'POST', body: formData });
                            const data = await res.json();
                            if (data.error === 'no_audio') {
                                appendMessage("Bot: I didn't catch that — please try again.", 'bot-message');
                                setOrbState('ready');
                                return;
                            }
                            await processBackendResponse(data);
                        } catch (err) {
                            console.error("Pipeline error:", err);
                            setOrbState('ready');
                        }
                    }
                };

                mediaRecorder.start(100);
                recordingStartTime = Date.now();
                setOrbState('listening');
            } catch (err) { console.error(err); }
        }
    });

    // ── Live Agent transfer ──────────────────────────────────────
    async function transferToHuman() {
        if (isFirstClick) {
            isFirstClick = false;
            chatBox.classList.add('visible');
        }
        appendMessage("You: Please connect me to a human representative.", 'user-message');
        const msg = "Connecting you to a human representative now. Please hold while I transfer your call.";
        appendMessage("Bot: " + msg, 'bot-message');
        await playAudio(msg);
        if (humanButton) {
            humanButton.disabled = true;
            humanButton.textContent = 'Transfer in progress';
        }
        orbButton.style.pointerEvents = 'none';
        orbButton.style.opacity = '0.4';
    }

    if (humanButton) {
        humanButton.addEventListener('click', transferToHuman);
    }

    orbButton.addEventListener('mouseup', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    });

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        themeToggle.innerText = isDark ? '🌙' : '🔅';
    });

    voiceToggle.addEventListener('click', () => {
        currentVoiceGender = currentVoiceGender === 'male' ? 'female' : 'male';
        voiceIcon.src = currentVoiceGender === 'male'
            ? '/frontend/male_icon.png'
            : '/frontend/female_icon.png';
    });

    resetButton.addEventListener('click', () => {
        const img = resetButton.querySelector('img');
        img.classList.remove('reset-spin');
        void img.offsetWidth;
        img.classList.add('reset-spin');

        currentStepIndex = 0;
        inTroubleshoot = false;
        currentIntent = 'other';
        currentState = 'ready';
        isFirstClick = true;

        orbStatus.innerText = "Push to Talk";
        orbButton.classList.remove('active');

        chatBox.innerHTML = '';
        chatBox.classList.remove('visible');

        if (humanButton) {
            humanButton.disabled = false;
            humanButton.textContent = 'Live Agent';
        }

        orbButton.style.pointerEvents = '';
        orbButton.style.opacity = '';
    });
});
