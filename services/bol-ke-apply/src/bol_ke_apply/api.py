"""FastAPI HTTP interface & interactive web UI for Bol Ke Apply (Module 6).

Complements the stdio MCP server by exposing HTTP endpoints and a browser-based
voice/text test console (Web Speech API enabled).
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from bol_ke_apply.agent import BolKeApplyAgent
from bol_ke_apply.server import check_mismatch, fetch_identity, match_video, whats_next

app = FastAPI(
    title="Bol Ke Apply — Voice & Conversational Front Door",
    version="0.1.0",
    description="Module 6: Conversational front door exposing Module 3 and Module 4 via MCP tools.",
)

agent = BolKeApplyAgent()


class ChatRequest(BaseModel):
    message: str
    applicant_id: str = "applicant_clean"
    journey_stage: str | None = None


class ToolFetchIdentityRequest(BaseModel):
    applicant_id: str


class ToolCheckMismatchRequest(BaseModel):
    applicant_id: str


class ToolMatchVideoRequest(BaseModel):
    applicant_id: str
    query: str
    journey_stage: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bol-ke-apply"}


@app.post("/chat")
def chat(request: ChatRequest) -> dict:
    """Process a voice transcript or text query through Bol Ke Apply."""
    return agent.interact(
        message=request.message,
        applicant_id=request.applicant_id,
        journey_stage=request.journey_stage,
    )


@app.get("/tools")
def list_tools() -> list[dict]:
    """Expose the 3 registered MCP platform tools."""
    return [
        {
            "name": "fetch_identity",
            "description": "Fetch verified citizen profile from DigiLocker / Aadhaar e-KYC (Module 3)",
            "parameters": {"applicant_id": "string"},
        },
        {
            "name": "check_mismatch",
            "description": "Perform rejection-prevention cross-check between Aadhaar and secondary records (Module 3)",
            "parameters": {"applicant_id": "string"},
        },
        {
            "name": "match_video",
            "description": "Match a driving difficulty to an instructional lesson clip (Module 4)",
            "parameters": {
                "applicant_id": "string",
                "query": "string",
                "journey_stage": "string | None",
            },
        },
        {
            "name": "whats_next",
            "description": "Get the citizen's journey stage and next action (Module 2)",
            "parameters": {"applicant_id": "string"},
        },
    ]


@app.post("/tools/fetch_identity")
def tool_fetch_identity(req: ToolFetchIdentityRequest) -> dict:
    return fetch_identity(applicant_id=req.applicant_id)


@app.post("/tools/check_mismatch")
def tool_check_mismatch(req: ToolCheckMismatchRequest) -> dict:
    return check_mismatch(applicant_id=req.applicant_id)


@app.post("/tools/match_video")
def tool_match_video(req: ToolMatchVideoRequest) -> dict:
    return match_video(
        applicant_id=req.applicant_id,
        query=req.query,
        journey_stage=req.journey_stage,
    )


class ToolWhatsNextRequest(BaseModel):
    applicant_id: str


@app.post("/tools/whats_next")
def tool_whats_next(req: ToolWhatsNextRequest) -> dict:
    return whats_next(applicant_id=req.applicant_id)


@app.get("/", response_class=HTMLResponse)
def interactive_console() -> str:
    """Interactive browser console with Web Speech voice recognition and bilingual chat."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bol Ke Apply — Parivahan MVP</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #1e3a8a;
      --accent: #f97316;
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #64748b;
      --border: #e2e8f0;
      --user-bubble: #1e3a8a;
      --bot-bubble: #f1f5f9;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .container { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
    header { background: var(--card); padding: 20px; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .badge { display: inline-block; background: #e0e7ff; color: #3730a3; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-bottom: 8px; }
    h1 { font-size: 24px; font-weight: 700; color: var(--primary); display: flex; align-items: center; gap: 8px; }
    p.sub { font-size: 14px; color: var(--muted); margin-top: 4px; }
    .persona-bar { display: flex; align-items: center; gap: 12px; margin-top: 12px; flex-wrap: wrap; }
    select { padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border); font-family: inherit; font-size: 13px; background: white; cursor: pointer; }
    .chat-box { background: var(--card); border-radius: 16px; border: 1px solid var(--border); height: 480px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
    .msg { max-width: 80%; padding: 12px 16px; border-radius: 14px; font-size: 14px; line-height: 1.5; }
    .msg.bot { align-self: flex-start; background: var(--bot-bubble); color: var(--text); border-bottom-left-radius: 4px; }
    .msg.user { align-self: flex-end; background: var(--user-bubble); color: white; border-bottom-right-radius: 4px; }
    .tool-tag { display: inline-block; font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 6px; margin-top: 6px; font-weight: 600; }
    .prompt-pills { display: flex; gap: 8px; padding: 10px 16px; background: #f8fafc; border-top: 1px solid var(--border); overflow-x: auto; }
    .pill { font-size: 12px; background: white; border: 1px solid var(--border); padding: 6px 12px; border-radius: 999px; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
    .pill:hover { background: #f1f5f9; border-color: #cbd5e1; }
    .input-bar { display: flex; gap: 8px; padding: 16px; background: white; border-top: 1px solid var(--border); align-items: center; }
    input[type="text"] { flex: 1; padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border); font-size: 14px; font-family: inherit; outline: none; }
    input[type="text"]:focus { border-color: var(--primary); }
    button { padding: 12px 20px; border-radius: 10px; border: none; cursor: pointer; font-family: inherit; font-weight: 600; font-size: 14px; transition: all 0.2s; }
    .btn-send { background: var(--primary); color: white; }
    .btn-send:hover { opacity: 0.9; }
    .btn-mic { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; display: flex; align-items: center; gap: 4px; }
    .btn-mic.recording { background: #fee2e2; color: #b91c1c; border-color: #fca5a5; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
  </style>
</head>
<body>
<div class="container">
  <header>
    <span class="badge">Module 6 • Bol Ke Apply</span>
    <h1>🎙️ बोल के अप्लाई — Voice Front Door</h1>
    <p class="sub">Speak or type in English, Hindi, or Hinglish. Backed by Module 3 (Identity) & Module 4 (Driving Academy) MCP tools.</p>
    <div class="persona-bar">
      <label for="persona" style="font-size: 13px; font-weight: 600;">Active Citizen Persona:</label>
      <select id="persona">
        <option value="applicant_clean">Rohan Verma (Clean pass • Indiranagar KA)</option>
        <option value="applicant_student_mover">Priya Sharma (Student mover • UP Aadhaar vs KA GPS)</option>
        <option value="applicant_pan_name_mismatch">Vikram Singh Chauhan (PAN name mismatch)</option>
        <option value="applicant_minor">Aryan Mehta (Minor 17y • Age ineligible)</option>
        <option value="applicant_dob_mismatch">Ananya Iyer (Aadhaar vs PAN DOB mismatch)</option>
      </select>
    </div>
  </header>

  <div class="chat-box">
    <div class="messages" id="messages">
      <div class="msg bot">
        नमस्ते! मैं 'बोल के अप्लाई' सहायक हूँ।<br>
        आप बोलकर अपना आधार प्रोफ़ाइल जाँच सकते हैं, दस्तावेज़ों का मिसमैच चेक कर सकते हैं या ड्राइविंग टेस्ट के टिप्स पूछ सकते हैं।
      </div>
    </div>

    <div class="prompt-pills">
      <div class="pill" onclick="sendQuick('Mera verified Aadhaar profile dikhao')">👤 Mera profile dikhao</div>
      <div class="pill" onclick="sendQuick('Check karo documents me koi mistake to nahi hai?')">⚠️ Check rejection risk</div>
      <div class="pill" onclick="sendQuick('clutch kaise chhodna hai gadi band ho jaati hai')">🚗 Clutch kaise chhodna hai</div>
      <div class="pill" onclick="sendQuick('8 track pe car kaise modna hai')">🔄 8-track steering tips</div>
      <div class="pill" onclick="sendQuick('रिवर्स पार्किंग का सही तरीका बताओ')">🅿️ रिवर्स पार्किंग का तरीका</div>
    </div>

    <div class="input-bar">
      <button class="btn-mic" id="micBtn" onclick="toggleVoice()" title="Click to speak (Voice Recognition)">🎙️ Speak</button>
      <input type="text" id="userInput" placeholder="Type or click Speak in English, Hindi, or Hinglish..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button class="btn-send" onclick="sendMessage()">Send</button>
    </div>
  </div>
</div>

<script>
  let recognition;
  let isRecording = false;

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'hi-IN'; // Supports Hindi/Hinglish/English

    recognition.onstart = () => {
      isRecording = true;
      document.getElementById('micBtn').classList.add('recording');
      document.getElementById('micBtn').innerHTML = '🔴 Listening...';
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      document.getElementById('userInput').value = transcript;
      sendMessage();
    };

    recognition.onerror = (e) => {
      console.warn('Speech recognition error:', e);
      stopVoice();
    };

    recognition.onend = () => {
      stopVoice();
    };
  }

  function toggleVoice() {
    if (!recognition) {
      alert('Voice recognition not supported in this browser. Please type your message.');
      return;
    }
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }

  function stopVoice() {
    isRecording = false;
    const btn = document.getElementById('micBtn');
    btn.classList.remove('recording');
    btn.innerHTML = '🎙️ Speak';
  }

  function sendQuick(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
  }

  async function sendMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text) return;

    const persona = document.getElementById('persona').value;
    const messages = document.getElementById('messages');

    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'msg user';
    userDiv.textContent = text;
    messages.appendChild(userDiv);
    input.value = '';
    messages.scrollTop = messages.scrollHeight;

    // Loading indicator
    const botDiv = document.createElement('div');
    botDiv.className = 'msg bot';
    botDiv.textContent = 'Thinking...';
    messages.appendChild(botDiv);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text, applicant_id: persona})
      });
      const data = await res.json();
      botDiv.innerHTML = data.reply.replace(/\\n/g, '<br>');
      if (data.tool_called) {
        const tag = document.createElement('div');
        tag.className = 'tool-tag';
        tag.textContent = '🛠️ Executed MCP Tool: ' + data.tool_called;
        botDiv.appendChild(tag);
      }
    } catch (err) {
      botDiv.textContent = 'Error connecting to Bol Ke Apply: ' + err.message;
    }
    messages.scrollTop = messages.scrollHeight;
  }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bol_ke_apply.api:app", host="127.0.0.1", port=8006, reload=True)
