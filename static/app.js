const thread = document.querySelector("#thread");
const messages = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const composer = document.querySelector("#composer");
const questionInput = document.querySelector("#question");
const sendButton = document.querySelector("#send-button");
const providerLabel = document.querySelector("#provider-label");

function scrollToLatest() {
  thread.scrollTop = thread.scrollHeight;
}

function addMessage(role, content, extraClass = "") {
  welcome.hidden = true;
  const message = document.createElement("article");
  message.className = `message message-${role} ${extraClass}`.trim();

  if (role === "assistant") {
    const mark = document.createElement("span");
    mark.className = "assistant-mark message-mark";
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = "C";
    message.append(mark);
  }

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;
  message.append(bubble);
  messages.append(message);
  scrollToLatest();
  return message;
}

async function loadConversation() {
  const [configResponse, historyResponse] = await Promise.all([
    fetch("/api/config"),
    fetch("/api/history"),
  ]);
  if (configResponse.ok) {
    const config = await configResponse.json();
    providerLabel.textContent = `${config.provider} · ${config.model}`;
  }
  if (historyResponse.ok) {
    const history = await historyResponse.json();
    for (const message of history.messages) {
      addMessage(message.role, message.content);
    }
  }
}

async function sendQuestion(question) {
  questionInput.value = "";
  addMessage("user", question);
  sendButton.disabled = true;
  questionInput.disabled = true;
  const pending = addMessage("assistant", "Thinking…", "message-pending");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const result = await response.json();
    pending.remove();
    if (!response.ok) {
      addMessage("assistant", result.error || "Something went wrong. Please try again.");
      return;
    }
    addMessage("assistant", result.answer);
  } catch {
    pending.remove();
    addMessage("assistant", "Could not reach the support service. Check that the local server is running, then try again.");
  } finally {
    sendButton.disabled = false;
    questionInput.disabled = false;
    questionInput.focus();
  }
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (question && !sendButton.disabled) sendQuestion(question);
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    composer.requestSubmit();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => sendQuestion(button.dataset.question));
});

document.querySelector("#new-chat").addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST" });
  messages.replaceChildren();
  welcome.hidden = false;
  questionInput.value = "";
  questionInput.focus();
});

loadConversation().catch(() => {
  providerLabel.textContent = "offline";
});