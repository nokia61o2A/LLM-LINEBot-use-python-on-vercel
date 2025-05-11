# api/index.py

import os
import io
import requests
from flask import Flask, request, abort
from api.llm import ChatGPT
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage,
    QuickReply, QuickReplyButton, MessageAction
)

# ✅ 檢查環境變數，防止 Vercel 未設定時報錯
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not channel_secret or not channel_token:
    raise RuntimeError("❌ LINE_CHANNEL_SECRET 或 LINE_CHANNEL_ACCESS_TOKEN 尚未設定，請到 Vercel 設定環境變數")

line_bot_api = LineBotApi(channel_token)
web_handler = WebhookHandler(channel_secret)

# ✅ 修正拼字錯誤 DEFALUT_TALKING -> DEFAULT_TALKING
working_status = os.getenv("DEFAULT_TALKING", "true").lower() == "true"

# ✅ Flask App 初始化
app = Flask(__name__)
chatgpt = ChatGPT()

@app.route("/")
def home():
    return "<h1>Hello World</h1>"

# ✅ LINE Webhook 接收端點
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400, "Missing X-Line-Signature")

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        web_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, "Invalid Signature")
    except Exception as e:
        app.logger.error(f"❌ Webhook 處理失敗: {e}")
        abort(500, f"Internal Server Error: {str(e)}")

    return "OK"

# ✅ 處理文字訊息
@web_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.user_id == 'Udeadbeefdeadbeefdeadbeefdeadbeef':
        return 'OK'

    global working_status

    if event.message.type != "text":
        return

    if event.message.text[:3] == "啟動":
        working_status = True
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="啟動AI"))
        return

    if event.message.text[:5] == "關閉AI":
        working_status = False
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='AI下班去，喚醒請輸入"啟動"'))
        return

    if working_status:
        start_loading_animation(event.source.user_id, 5)
        chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")

        questions = ["了解更多", "出2個練習題", "相關觀念", "關閉AI"]
        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label=question, text=question))
            for question in questions
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"助教:{reply_msg}",
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        )

# ✅ 處理圖片訊息
@web_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    image_content = line_bot_api.get_message_content(event.message.id)
    path = chatgpt.get_user_image(image_content)
    link = chatgpt.upload_img_link(path)
    response = chatgpt.process_image_link(link)
    reply_msg = response['choices'][0]['text']
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"助教:{reply_msg}"))

# ✅ Vercel 不需要 app.run()
# if __name__ == "__main__": app.run() ❌ 請勿保留這段