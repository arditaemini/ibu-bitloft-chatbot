// Created by the BITLoft Team, International Balkan University.
const messagesEl = document.getElementById("messages");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const statusEl = document.getElementById("status");
const suggestionsEl = document.getElementById("suggestions");
const clearBtn = document.getElementById("clear");
const initialMessages = messagesEl.innerHTML;

let history = [];
let busy = false;

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Minimal, safe Markdown: escapes HTML first, then handles bold, italics, links and lists.
function renderMarkdown(text) {
  const inline = (s) =>
    escapeHtml(s)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|[\s(])([\w.+-]+@[\w-]+\.[\w.-]+\w)/g, '$1<a href="mailto:$2">$2</a>');

  let html = "";
  let list = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)/);
    const numbered = line.match(/^\d+[.)]\s+(.*)/);
    const type = bullet ? "ul" : numbered ? "ol" : null;
    if (type) {
      if (list !== type) { if (list) html += `</${list}>`; html += `<${type}>`; list = type; }
      html += `<li>${inline((bullet || numbered)[1])}</li>`;
      continue;
    }
    if (list) { html += `</${list}>`; list = null; }
    if (line) html += `<p>${inline(line.replace(/^#+\s*/, ""))}</p>`;
  }
  if (list) html += `</${list}>`;
  return html;
}

function addMessage(role, text, sources = []) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = role === "user" ? escapeHtml(text) : renderMarkdown(text);
  if (sources.length) {
    const s = document.createElement("div");
    s.className = "sources";
    s.textContent = "Sources: " + sources.join(", ");
    bubble.appendChild(s);
  }
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function showTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg bot";
  wrap.innerHTML = '<div class="bubble typing"><span></span><span></span><span></span></div>';
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

async function send(text) {
  text = text.trim();
  if (!text || busy) return;
  busy = true;
  sendBtn.disabled = true;
  suggestionsEl.hidden = true;
  addMessage("user", text);
  input.value = "";
  autoGrow();
  const typing = showTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: history.slice(-6) }),
    });
    const data = await res.json().catch(() => ({}));
    typing.remove();
    if (!res.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.";
      addMessage("bot error", detail);
      return;
    }
    addMessage("bot", data.answer, data.sources || []);
    history.push({ role: "user", content: text }, { role: "assistant", content: data.answer });
  } catch {
    typing.remove();
    addMessage("bot error", "Could not reach the server. Check that it is running and try again.");
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

function autoGrow() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
}

form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
input.addEventListener("input", autoGrow);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
});
suggestionsEl.addEventListener("click", (e) => {
  if (e.target.tagName === "BUTTON") send(e.target.textContent);
});
clearBtn.addEventListener("click", () => {
  history = [];
  messagesEl.innerHTML = initialMessages;
  suggestionsEl.hidden = false;
  input.focus();
});

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.ready) {
      statusEl.textContent = "Online";
      statusEl.className = "status ok";
    } else {
      statusEl.textContent = data.error || "Starting…";
      statusEl.className = "status err";
    }
  } catch {
    statusEl.textContent = "Offline";
    statusEl.className = "status err";
  }
}
checkHealth();
