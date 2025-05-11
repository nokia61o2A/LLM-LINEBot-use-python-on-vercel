# api/llm.py

import os
import requests
import pyimgur
from openai import OpenAI
from api.prompt import Prompt

class ChatGPT:
    """
    ChatGPT 處理類別，整合文字與圖片回覆。
    """

    def __init__(self):
        self.prompt = Prompt()

        self.model = os.getenv("OPENAI_MODEL", default="gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", default=0.0))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", default=600))

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("❌ OPENAI_API_KEY 環境變數未設定")

        base_url = os.getenv("OPENAI_BASE_URL", default="https://free.v36.cm/v1")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_response(self):
        """
        產生文字回覆。
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.prompt.generate_prompt(),
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def add_msg(self, text):
        """
        新增對話訊息到 prompt。
        """
        self.prompt.add_msg(text)

    def process_image_link(self, image_url):
        """
        處理圖片 URL，使用 OpenAI 分析圖片。
        """
        response = self.client.Completion.create(
            engine="davinci",
            prompt=f"Analyze the text in this image: {image_url}",
            max_tokens=100
        )
        return response

    def get_user_image(self, image_content):
        """
        將 LINE 傳來的圖片儲存為暫存檔。
        """
        path = './static/temp.png'
        with open(path, 'wb') as fd:
            for chunk in image_content.iter_content():
                fd.write(chunk)
        return path

    def upload_img_link(self, imgpath):
        """
        上傳圖片至 imgur 並取得公開 URL。
        """
        IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
        if not IMGUR_CLIENT_ID:
            raise RuntimeError("❌ IMGUR_CLIENT_ID 環境變數未設定")

        im = pyimgur.Imgur(IMGUR_CLIENT_ID)
        uploaded_image = im.upload_image(imgpath, title="Uploaded with PyImgur")
        return uploaded_image.link