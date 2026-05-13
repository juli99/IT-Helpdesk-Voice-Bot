const KB = {
  vpn: [
    "Restart the VPN client and reconnect.",
    "Check that your internet connection is stable.",
    "Disable and re-enable your network adapter."
  ],
  email: [
    "Sign out and sign back into Outlook.",
    "Clear cached credentials from Credential Manager.",
    "Remove and re-add the email account."
  ],
  login: [
    "Verify your username and password.",
    "Make sure Caps Lock is turned off.",
    "Reset your password if needed."
  ],
  network: [
    "Restart your router or modem.",
    "Check if other devices can access the internet.",
    "Run a network diagnostic test."
  ],
  software: [
    "Restart the application.",
    "Check for available software updates.",
    "Reinstall the application if the issue continues."
  ],
  hardware: [
    "Restart the device.",
    "Check all cable connections.",
    "Test the device on another computer if possible."
  ],
  other: [
    "Please describe the issue in more detail.",
    "Let me connect you with a specialist.",
    "I will escalate this issue to the support team."
  ]
};

let topic = null;
let stepIndex = 0;

function startTroubleshooting(selectedTopic) {
  topic = selectedTopic;
  stepIndex = 0;
  offerNextStep();
}

function offerNextStep() {
  const steps = KB[topic
  ];

  if (stepIndex >= steps.length) {
    escalateToTier2();
    return;
  }

  const currentStep = steps[stepIndex
  ];
  stepIndex++;

  console.log(`Bot: Please try the following — "${currentStep}"`);
  askIfResolved();
}

function askIfResolved() {
  // Replace this with your actual user-input mechanism (button, prompt, etc.)
  const resolved = confirm("Did that fix your issue?");

  if (resolved) {
    console.log("Bot: Great! Glad the issue is resolved. Have a nice day!");
  } else {
    offerNextStep();
  }
}

function escalateToTier2() {
  console.log("Bot: All troubleshooting steps have been exhausted. Escalating to support...");
  // Add your Tier 2 escalation logic here (e.g., open a ticket, notify an agent)
}