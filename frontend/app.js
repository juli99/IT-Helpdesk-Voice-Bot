// document.addEventListener('DOMContentLoaded', () => {
//     const orbButton = document.getElementById('orbButton');
//     const orbStatus = document.getElementById('orbStatus');
//     const lottieContainerPink = document.getElementById('lottieContainerPink');
//     const lottieContainerGreen = document.getElementById('lottieContainerGreen');
//     const chatBox = document.getElementById('chatBox');
//     const themeToggle = document.getElementById('themeToggle');
//     const voiceToggle = document.getElementById('voiceToggle');
//     const voiceIcon = document.getElementById('voiceIcon');
//     const resetButton = document.getElementById('resetButton');

//     let currentVoiceGender = 'male';
//     let currentState = 'ready';
//     let isFirstClick = true;
//     let mediaRecorder;
//     let audioChunks = [];

//     let currentTopic = null;
//     let currentStepIndex = 0;

//     voiceIcon.src = '/frontend/female_icon.png';

//     let animationPink = lottie.loadAnimation({
//         container: lottieContainerPink,
//         renderer: 'svg', loop: true, autoplay: false,
//         path: '/frontend/wave_pink.json'
//     });

//     let animationGreen = lottie.loadAnimation({
//         container: lottieContainerGreen,
//         renderer: 'svg', loop: true, autoplay: false,
//         path: '/frontend/wave_green.json'
//     });

//     async function handleTroubleshooting(userInput, data) {

//         if (typeof KB === 'undefined') {
//             console.error("Knowledge Base (KB) is not loaded!");
//             return;
//         }

//         const text = userInput.toLowerCase();

//         if (currentTopic) {
//             if (text.includes("no") || text.includes("not working") || text.includes("didn't")) {
//                 currentStepIndex++;
//                 const steps = KB[currentTopic];

//                 if (steps && currentStepIndex < steps.length) {
//                     const nextStep = steps[currentStepIndex];
//                     const reply = `I'm sorry. Let's try this: ${nextStep}. Does that help?`;
//                     appendMessage("Bot: " + reply, 'bot-message');
//                     await playAudio(reply);
//                 } else {
//                     const reply = "I've exhausted all standard steps. I'm escalating your ticket to Tier 2 for further investigation.";
//                     appendMessage("Bot: " + reply, 'bot-message');
//                     await playAudio(reply);
//                     currentTopic = null;
//                 }
//                 return;
//             }

//             if (text.includes("yes") || text.includes("fixed") || text.includes("worked")) {
//                 const reply = "Great! I'm glad it's resolved. Have a productive day!";
//                 appendMessage("Bot: " + reply, 'bot-message');
//                 await playAudio(reply);
//                 currentTopic = null;
//                 return;
//             }
//         }

//         const detectedIntent = data.intent || (data.metadata && data.metadata.intent);
//         const detectedTier = data.tier || (data.metadata && data.metadata.tier);

//         if (detectedIntent) {
//             currentTopic = detectedIntent.toLowerCase();
//             currentStepIndex = 0;

//             if (detectedTier === "2") {
//                 const reply = "[URGENT] I've identified a critical system issue. I am opening an immediate Tier 2 ticket.";
//                 appendMessage("Bot: " + reply, 'bot-message');
//                 await playAudio(reply);
//                 currentTopic = null;
//             } else {
//                 const steps = KB[currentTopic] || KB['other'];
//                 const firstStep = steps[0];
//                 const reply = `I've identified a ${currentTopic} issue. Before opening a ticket, please try this: ${firstStep}. Did that work?`;
//                 appendMessage("Bot: " + reply, 'bot-message');
//                 await playAudio(reply);
//             }
//         }
//     }

//     async function playAudio(text) {
//         try {
//             const response = await fetch('/speak', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ text: text, voice_id: currentVoiceGender })
//             });
//             const data = await response.json();
//             if (data.audio) {
//                 const audio = new Audio("data:audio/mpeg;base64," + data.audio);
//                 setOrbState('speaking');
//                 audio.play().catch(e => { console.error(e); setOrbState('ready'); });
//                 audio.onended = () => setOrbState('ready');
//             } else { setOrbState('ready'); }
//         } catch (e) { console.error(e); setOrbState('ready'); }
//     }

//     function setOrbState(state) {
//         currentState = state;
//         animationPink.stop(); animationGreen.stop();
//         lottieContainerPink.style.opacity = 0; lottieContainerGreen.style.opacity = 0;
//         if (state === 'ready') {
//             orbButton.classList.remove('active');
//             orbStatus.innerText = "Push to Talk";
//         } else if (state === 'listening') {
//             orbButton.classList.add('active');
//             orbStatus.innerText = "Listening";
//             lottieContainerGreen.style.opacity = 1;
//             animationGreen.goToAndPlay(0, true);
//         } else if (state === 'processing') {
//             orbStatus.innerText = "Thinking...";
//         } else if (state === 'speaking') {
//             orbButton.classList.add('active');
//             orbStatus.innerText = "Speaking";
//             lottieContainerPink.style.opacity = 1;
//             animationPink.goToAndPlay(0, true);
//         }
//     }

//     function appendMessage(text, className) {
//         const msg = document.createElement('div');
//         msg.classList.add('message', className);
//         chatBox.appendChild(msg);
//         chatBox.scrollTop = chatBox.scrollHeight;
//         typeWriterElement(text, msg);
//     }

//     function typeWriterElement(text, element, speed = 30) {
//         element.textContent = "";
//         let i = 0;
//         function type() {
//             if (i < text.length) {
//                 element.textContent += text.charAt(i);
//                 i++;
//                 chatBox.scrollTop = chatBox.scrollHeight;
//                 setTimeout(type, speed);
//             }
//         }
//         type();
//     }

//     orbButton.addEventListener('mousedown', async () => {
//         if (window.AudioContext) {
//             const ctx = new AudioContext();
//             if (ctx.state === 'suspended') await ctx.resume();
//         }

//         if (isFirstClick) {
//             isFirstClick = false;
//             chatBox.classList.add('visible');
//             const welcome = "Hello, I am your IT assistant. How can I help you today?";
//             appendMessage("Bot: " + welcome, 'bot-message');
//             await playAudio(welcome);
//             return;
//         }

//         if (currentState === 'ready') {
//             try {
//                 const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//                 mediaRecorder = new MediaRecorder(stream);
//                 audioChunks = [];
//                 mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);

//                 mediaRecorder.onstop = async () => {
//                     const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
//                     setOrbState('processing');
//                     const formData = new FormData();
//                     formData.append('file', audioBlob, 'recording.wav');

//                     try {
//                         const response = await fetch('/transcribe', { method: 'POST', body: formData });
//                         const data = await response.json();

//                         if (data.text) {
//                             appendMessage("You: " + data.text, 'user-message');
//                             await handleTroubleshooting(data.text, data);
//                         } else {
//                             setOrbState('ready');
//                         }
//                     } catch (err) {
//                         console.error("Server error:", err);
//                         setOrbState('ready');
//                     }
//                 };

//                 mediaRecorder.start();
//                 setOrbState('listening');
//             } catch (err) { console.error(err); }
//         }
//     });

//     orbButton.addEventListener('mouseup', () => {
//         if (mediaRecorder && mediaRecorder.state === 'recording') {
//             mediaRecorder.stop();
//             mediaRecorder.stream.getTracks().forEach(track => track.stop());
//         }
//     });

//     themeToggle.addEventListener('click', () => {
//         const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
//         document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
//         themeToggle.innerText = isDark ? '🌙' : '🔅';
//     });

//     voiceToggle.addEventListener('click', () => {
//         currentVoiceGender = currentVoiceGender === 'male' ? 'female' : 'male';
//         voiceIcon.src = currentVoiceGender === 'male' ? '/frontend/female_icon.png' : '/frontend/male_icon.png';
//     });

//     resetButton.addEventListener('click', () => {
//         const img = resetButton.querySelector('img');

//         img.classList.remove('reset-spin');
//         void img.offsetWidth;
//         img.classList.add('reset-spin');

//         currentTopic = null;
//         currentStepIndex = 0;
//         currentState = 'ready';

//         orbStatus.innerText = "Push to Talk";
//         orbButton.classList.remove('active');

//         chatBox.innerHTML = '';
//         chatBox.classList.remove('visible');
//     });

// });


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

    let currentVoiceGender = 'male';
    let currentState = 'ready';
    let isFirstClick = true;
    let mediaRecorder;
    let audioChunks = [];

    let currentStepIndex = 0;
    let isResolved = false;

    // החזרת הנתיב המקורי שלך
    voiceIcon.src = '/frontend/female_icon.png';

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

    async function processBackendResponse(data) {
        if (data.error) {
            console.error("Backend Error:", data.error);
            setOrbState('ready');
            return;
        }

        if (data.corrected_transcript) {
            appendMessage("You: " + data.corrected_transcript, 'user-message');
        }

        const action = data.action;
        const botMessage = data.bot_message;

        if (botMessage) {
            appendMessage("Bot: " + botMessage, 'bot-message');
            await playAudio(botMessage);
        }

        if (data.step !== undefined) {
            currentStepIndex = data.step;
            console.log(`[State Debug] Updated step from server to: ${currentStepIndex}`);
        }

        if (data.resolved !== undefined) {
            isResolved = data.resolved;
            console.log(`[State Debug] Updated resolved status from server to: ${isResolved}`);
        }
        // ───────────────────────────────────────────────────────────────────

        if (action === "escalate" || action === "close") {
            currentStepIndex = 0;
            isResolved = false;

            if (data.ticket) {
                console.log("Ticket generated system action:", data.ticket);
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
            return; // בלחיצה הראשונה מברך ויוצא, זה בסדר גמור
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

                    console.log(`[Audio Debug] Sending audio size: ${audioBlob.size} bytes, Type: ${supportedMime}`);

                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.webm');
                    formData.append('step', currentStepIndex);
                    formData.append('resolved', isResolved);
                    formData.append('voice_id', currentVoiceGender);

                    try {
                        const response = await fetch('/process', { method: 'POST', body: formData });
                        const data = await response.json();
                        await processBackendResponse(data);
                    } catch (err) {
                        console.error("Server error during pipeline process:", err);
                        setOrbState('ready');
                    }
                };

                mediaRecorder.start();
                setOrbState('listening');
            } catch (err) { console.error(err); }
        }
    });

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
        if (currentVoiceGender === 'male') {
            currentVoiceGender = 'female';
            voiceIcon.src = '/frontend/male_icon.png';
        } else {
            currentVoiceGender = 'male';
            voiceIcon.src = '/frontend/female_icon.png';
        }
    });

    resetButton.addEventListener('click', () => {
        const img = resetButton.querySelector('img');
        img.classList.remove('reset-spin');
        void img.offsetWidth;
        img.classList.add('reset-spin');

        currentStepIndex = 0;
        isResolved = false;
        currentState = 'ready';
        isFirstClick = true;

        orbStatus.innerText = "Push to Talk";
        orbButton.classList.remove('active');

        chatBox.innerHTML = '';
        chatBox.classList.remove('visible');
    });
});