import requests
import uuid
import base64
import pyaudio

from huoshan_env_setting import MY_HUOSHAN_APPID, MY_HUOSHAN_TOKEN

class TextToSpeech:
    def __init__(self, appid, token, uid):
        self.appid = appid
        self.token = token
        self.uid = uid
        self.api_url = "https://openspeech.bytedance.com/api/v1/tts"

    def synthesize_and_play(self, text):
        reqid = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer;{self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "app": {
                "appid": self.appid,
                "token": self.token,
                "cluster": "volcano_tts"
            },
            "user": {
                "uid": self.uid
            },
            "audio": {
                "voice_type": "zh_female_cancan_mars_bigtts",
                "encoding": "pcm",
                "speed_ratio": 1.0
            },
            "request": {
                "reqid": reqid,
                "text": text,
                "operation": "query"
            }
        }

        response = requests.post(self.api_url, json=payload, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 3000:
                audio_data_base64 = response_data.get("data")
                audio_data = base64.b64decode(audio_data_base64)
                
                # 保存音频文件
                pcm_file_path = "output.pcm"
                with open(pcm_file_path, "wb") as audio_file:
                    audio_file.write(audio_data)
                
                print("音频合成成功，已保存为 output.pcm")
                self.play_pcm(pcm_file_path)
            else:
                print(f"请求失败，错误信息: {response_data.get('message')}")
        else:
            print(f"HTTP 请求失败，状态码: {response.status_code}")

    def play_pcm(self, file_path, sample_rate=24000, channels=1, sample_width=2):
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(sample_width),
                        channels=channels,
                        rate=sample_rate,
                        output=True)

        with open(file_path, 'rb') as pcm_file:
            chunk = 1024
            data = pcm_file.read(chunk)
            while data:
                stream.write(data)
                data = pcm_file.read(chunk)

        stream.stop_stream()
        stream.close()
        p.terminate()

# 使用示例
if __name__ == '__main__':
    appid = MY_HUOSHAN_APPID
    token = MY_HUOSHAN_TOKEN
    uid = "your_uid"
    text = "我不饿，你们去吃吧"

    tts = TextToSpeech(appid, token, uid)
    tts.synthesize_and_play(text)