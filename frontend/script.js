document.addEventListener('DOMContentLoaded', () => {
    const orbButton = document.getElementById('orbButton');
    const orbStatus = document.getElementById('orbStatus');
    const lottieContainerPink = document.getElementById('lottieContainerPink');
    const lottieContainerGreen = document.getElementById('lottieContainerGreen');
    const chatBox = document.getElementById('chatBox');
    const botResponseSpan = document.getElementById('botResponse');
    const userTextSpan = document.getElementById('userText');
    const themeToggle = document.getElementById('themeToggle');
    const voiceToggle = document.getElementById('voiceToggle');
    const voiceIcon = document.getElementById('voiceIcon');

    let currentVoiceGender = 'male';
    voiceIcon.src = '/frontend/female_icon.png';
    let currentState = 'ready';
    let isFirstClick = true;

    voiceIcon.src = currentVoiceGender === 'male'
        ? '/frontend/female_icon.png'
        : '/frontend/male_icon.png';

    let animationPink = lottie.loadAnimation({
        container: lottieContainerPink,
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: '/frontend/wave_pink.json'
    });

    let animationGreen = lottie.loadAnimation({
        container: lottieContainerGreen,
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: '/frontend/wave_green.json'
    });

    let currentAnimation = animationPink;

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = SpeechRec ? new SpeechRec() : null;
    if (recognition) {
        recognition.lang = 'en-US';
        recognition.interimResults = false;
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

                audio.play().catch(e => {
                    console.error("Playback failed:", e);
                    setOrbState('ready');
                });

                audio.onended = () => {
                    setOrbState('ready');
                };
            } else {
                setOrbState('ready');
            }
        } catch (e) {
            console.error("Fetch error:", e);
            setOrbState('ready');
        }
    }

    function setOrbState(state) {
        currentState = state;
        animationPink.stop();
        animationGreen.stop();
        lottieContainerPink.style.opacity = 0;
        lottieContainerGreen.style.opacity = 0;

        if (state === 'ready') {
            orbButton.classList.remove('active');
            orbStatus.innerText = "Push to Talk";
        } else if (state === 'listening') {
            orbButton.classList.add('active');
            orbStatus.innerText = "Listening";
            lottieContainerGreen.style.opacity = 1;
            animationGreen.goToAndPlay(0, true);
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

    orbButton.addEventListener('click', async () => {
        if (window.AudioContext) {
            const ctx = new AudioContext();
            if (ctx.state === 'suspended') await ctx.resume();
        }

        if (isFirstClick) {
            isFirstClick = false;
            const welcome = "Hello, I am your IT assistant. How can I help you today?";
            chatBox.classList.add('visible');
            appendMessage("Bot: " + welcome, 'bot-message');
            await playAudio(welcome);
            return;
        }

        if (currentState === 'ready' && recognition) {
            setOrbState('listening');
            recognition.start();
        }
    });

    if (recognition) {
        recognition.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            appendMessage("You: " + transcript, 'user-message');
            const reply = "I am processing your request regarding " + transcript;
            setTimeout(async () => {
                appendMessage("Bot: " + reply, 'bot-message');
                await playAudio(reply);
            }, 500);
        };
        recognition.onerror = () => setOrbState('ready');
    }

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        themeToggle.innerText = isDark ? '🌙' : '🔅';
    });

    voiceToggle.addEventListener('click', () => {
        currentVoiceGender = currentVoiceGender === 'male' ? 'female' : 'male';
        voiceIcon.src = currentVoiceGender === 'male' ? '/frontend/female_icon.png' : '/frontend/male_icon.png';
    });
});