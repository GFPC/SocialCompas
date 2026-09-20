import asyncio
import logging
from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

import config
from transport import MaxBotTransport, parse_update, CallbackEvent, MessageEvent
from fsm import MemoryStorage
from handlers import Dispatcher

logger = logging.getLogger("simulator")
logging.basicConfig(level=logging.INFO)

# Dummy transport capturing sent messages for web UI simulation
class SimTransport(MaxBotTransport):
    def __init__(self):
        super().__init__()
        self.last_response = {}

    async def send_message(self, chat_id, text, keyboard=None):
        buttons = []
        if keyboard:
            buttons = keyboard
        self.last_response = {
            "chat_id": str(chat_id),
            "text": text,
            "keyboard": {"inline_keyboard": buttons}
        }
        return {"ok": True}

    async def answer_callback(self, callback_id, notification="ОК"):
        return {"ok": True}


sim_transport = SimTransport()
storage = MemoryStorage()
dp = Dispatcher(transport=sim_transport, storage=storage)

app = FastAPI(title="MAX Bot SocialCompas Simulator")


@app.get("/", response_class=HTMLResponse)
async def get_simulator_ui():
    """Renders a simple clean Web UI chat interface for testing MAX Bot."""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>MAX Bot - SocialCompas Simulator</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
            .chat-container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column; height: 85vh; }
            .chat-header { background: #2b5278; color: white; padding: 16px; font-weight: bold; font-size: 18px; display: flex; justify-content: space-between; align-items: center; }
            .badge { background: #4caf50; font-size: 12px; padding: 4px 8px; border-radius: 12px; font-weight: normal; }
            .chat-messages { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 10px; line-height: 1.4; word-wrap: break-word; white-space: pre-wrap; }
            .msg.user { align-self: flex-end; background: #2b5278; color: white; border-bottom-right-radius: 2px; }
            .msg.bot { align-self: flex-start; background: #eef2f5; color: #1c2b36; border-bottom-left-radius: 2px; border: 1px solid #dcdfe6; }
            .keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
            .keyboard-row { display: flex; gap: 6px; }
            .btn { flex: 1; padding: 8px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; text-align: center; font-size: 14px; transition: background 0.2s; }
            .btn:hover { background: #2563eb; }
            .chat-input { display: flex; border-top: 1px solid #eef2f5; padding: 12px; background: #fafafa; gap: 8px; }
            .chat-input input { flex: 1; padding: 10px; border: 1px solid #dcdfe6; border-radius: 6px; font-size: 14px; outline: none; }
            .chat-input button { padding: 10px 18px; background: #2b5278; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <span>🤖 SocialCompas (MAX Bot Simulator)</span>
                <span class="badge">Local Sandbox Mode</span>
            </div>
            <div class="chat-messages" id="messages"></div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="Введите команду (/start, /compass) или сообщение..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Отправить</button>
            </div>
        </div>

        <script>
            async function sendMessage(textOverride = null, isCallback = false) {
                const input = document.getElementById("userInput");
                const text = textOverride || input.value.trim();
                if (!text && !isCallback) return;
                
                if (!textOverride) input.value = "";
                
                appendMessage(text, "user");
                
                let payload = {};
                if (isCallback) {
                    payload = { callback_query: { data: text, from: { id: "sim_user_1" }, message: { chat: { id: "sim_chat_1" } } } };
                } else {
                    payload = { message: { text: text, chat: { id: "sim_chat_1" }, from: { id: "sim_user_1" } } };
                }

                const res = await fetch("/api/simulate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                appendBotMessage(data.text, data.keyboard);
            }

            function appendMessage(text, sender) {
                const msgs = document.getElementById("messages");
                const div = document.createElement("div");
                div.className = "msg " + sender;
                div.textContent = text;
                msgs.appendChild(div);
                msgs.scrollTop = msgs.scrollHeight;
            }

            function appendBotMessage(text, keyboard) {
                const msgs = document.getElementById("messages");
                const div = document.createElement("div");
                div.className = "msg bot";
                
                let html = (text || "").replace(/\\*(.*?)\\*/g, "<b>$1</b>");
                div.innerHTML = html;

                if (keyboard && keyboard.inline_keyboard) {
                    const kbDiv = document.createElement("div");
                    kbDiv.className = "keyboard";
                    keyboard.inline_keyboard.forEach(row => {
                        const rowDiv = document.createElement("div");
                        rowDiv.className = "keyboard-row";
                        row.forEach(btn => {
                            const btnElem = document.createElement("button");
                            btnElem.className = "btn";
                            btnElem.textContent = btn.text;
                            btnElem.onclick = () => sendMessage(btn.callback_data || btn.url || btn.text, true);
                            rowDiv.appendChild(btnElem);
                        });
                        kbDiv.appendChild(rowDiv);
                    });
                    div.appendChild(kbDiv);
                }

                msgs.appendChild(div);
                msgs.scrollTop = msgs.scrollHeight;
            }

            window.onload = () => sendMessage("/start");
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/simulate")
async def simulate_update(request: Request):
    update = await request.json()
    sim_transport.last_response = {}
    await dp.feed_update(update)
    return sim_transport.last_response


async def run_cli_simulator():
    """Runs interactive CLI simulator in terminal."""
    print("\n" + "=" * 50)
    print("🤖 MAX BOT SIMULATOR - LOCAL TERMINAL MODE")
    print("Введите /start, /compass, /info, /echo <текст> или exit для выхода")
    print("=" * 50 + "\n")

    chat_id = "cli_user"
    update = {"message": {"text": "/start", "chat": {"id": chat_id}}}
    await dp.feed_update(update)
    res = sim_transport.last_response
    print(f"🤖 Bot:\n{res.get('text', '')}\n")

    while True:
        try:
            user_input = input("\n👤 Вы: ").strip()
            if user_input.lower() in ("exit", "quit"):
                print("Выход из симулятора.")
                break
            if not user_input:
                continue

            if user_input.startswith("cb:"):
                cb_data = user_input[3:].strip()
                update = {"callback_query": {"data": cb_data, "message": {"chat": {"id": chat_id}}}}
            else:
                update = {"message": {"text": user_input, "chat": {"id": chat_id}}}

            await dp.feed_update(update)
            res = sim_transport.last_response
            print(f"\n🤖 Bot:\n{res.get('text', '')}")
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение работы симулятора.")
            break


def start_web_simulator(host: str = config.HOST, port: int = config.PORT):
    print(f"🚀 Запуск веб-симулятора MAX Bot на http://localhost:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv:
        asyncio.run(run_cli_simulator())
    else:
        start_web_simulator()
