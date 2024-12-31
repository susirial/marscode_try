import requests
import uuid
import base64

from huoshan_env_setting import MY_HUOSHAN_APPID, MY_HUOSHAN_TOKEN

def synthesize_speech(appid, token, uid, text):
    api_url = "https://openspeech.bytedance.com/api/v1/tts"
    
    # 生成唯一的请求ID
    reqid = str(uuid.uuid4())
    
    # 请求头
    headers = {
        "Authorization": f"Bearer;{token}",
        "Content-Type": "application/json"
    }
    
    # 请求体
    payload = {
        "app": {
            "appid": appid,
            "token": token,
            "cluster": "volcano_tts"
        },
        "user": {
            "uid": uid
        },
        "audio": {
            "voice_type": "zh_female_cancan_mars_bigtts",
            "encoding": "mp3",
            "speed_ratio": 1.0
        },
        "request": {
            "reqid": reqid,
            "text": text,
            "operation": "query"
        }
    }
    
    # 发送请求
    response = requests.post(api_url, json=payload, headers=headers)
    
    # 处理响应
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("code") == 3000:
            audio_data_base64 = response_data.get("data")
            audio_data = base64.b64decode(audio_data_base64)
            
            # 保存音频文件
            with open("output.mp3", "wb") as audio_file:
                audio_file.write(audio_data)
            
            print("音频合成成功，已保存为 output.mp3")
        else:
            print(f"请求失败，错误信息: {response_data.get('message')}")
    else:
        print(f"HTTP 请求失败，状态码: {response.status_code}")

# 使用示例
if __name__ == '__main__':
    appid = MY_HUOSHAN_APPID
    token = MY_HUOSHAN_TOKEN
    uid = "your_uid"
    text = "错误原因：传入的 text 无效，没有可合成的有效文本。比如全部是标点符号或者 emoji 表情"

    synthesize_speech(appid, token, uid, text)
    pass