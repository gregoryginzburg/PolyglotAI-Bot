import aiohttp


class YandexAPI:
    url_recognize = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    url_translate = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    url_synthesize = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    def __init__(self, token, folderid):
        self.IAM_TOKEN = token
        self.folder_id = folderid

    async def transcribe(self, file_data):
        params = {
            "folderId": self.folder_id,
            "lang": "ru-RU",
            "topic": "general"
        }
        headers = {
            "Authorization": f"Bearer {self.IAM_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url_recognize, params=params, data=file_data, headers=headers) as response:
                t = await response.json()
                return t.get('result')

    async def synthesize(self, text):
        params = {
            "text": text,
            "format": "mp3",
            "folderId": self.folder_id,
            "emotion": "good"
        }
        headers = {
            "Authorization": f"Bearer {self.IAM_TOKEN}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url_synthesize, data=params, headers=headers) as response:
                t = await response.content.read()
                return t

    async def translate(self, text, target_language):
        texts = [text]

        body = {
            "targetLanguageCode": target_language,
            "texts": texts,
            "folderId": self.folder_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(self.IAM_TOKEN)
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url_translate, json=body, headers=headers) as response:
                t = await response.json()
                return t['translations'][0]['text']
