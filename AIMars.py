import requests
import json
import uuid
import threading
import pyaudio
import time
import nls
import base64
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import io
from urllib.request import urlopen

from coze_env_setting import MY_BOT_ID, MY_COZE_TOKEN
from huoshan_env_setting import MY_HUOSHAN_APPID, MY_HUOSHAN_TOKEN
from text2speech_tool import TextToSpeech
from ali_env_setting import MY_ALI_APPKEY, MY_ALI_TOKEN

YOUR_BOT_ID = MY_BOT_ID
YOUR_COZE_TOKEN = MY_COZE_TOKEN

# 文本转语音
huoshan_appid = MY_HUOSHAN_APPID
huoshan_token = MY_HUOSHAN_TOKEN
huoshan_uid = str(uuid.uuid4())

ALI_TOKEN = MY_ALI_TOKEN
ALI_APPKEY = MY_ALI_APPKEY

URL = "wss://nls-gateway-cn-beijing.aliyuncs.com/ws/v1"
TOKEN = ALI_TOKEN
APPKEY = ALI_APPKEY

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

class MyChatBot:
    def __init__(self, display_callback):
        self.messages = []
        self.input_value = ''
        self.conversation_id = None
        self.bot_id = YOUR_BOT_ID
        self.user_id = self.generate_uuid()
        self.current_message = ''
        self.tts = TextToSpeech(huoshan_appid, huoshan_token, huoshan_uid)
        self.is_processing = False
        self.display_callback = display_callback
        self.user_message = ''
        # 初始化锁
        self.lock = threading.Lock()

        # 最后生成的图片URL
        self.pic_url = ''

    def generate_uuid(self):
        return str(uuid.uuid4())

    def send_message(self):
        if self.is_processing:
            self.display_callback("AI正在处理，跳过发送")
            return

        self.is_processing = True
        message = self.input_value
        if not message:
            self.is_processing = False
            return

        if not self.conversation_id:
            self.create_empty_conversation()
            if not self.conversation_id:
                self.is_processing = False
                self.display_callback("无法创建对话!!")
                return

        self.messages.append({'role': 'user', 'content': message})
        self.input_value = ''

        #提供一个上下文
        msg_to_coze = '用户当前输入: ' + message + '\n' + '用户之前让AI生成的图片：' + self.pic_url

        self.display_user_message(message)

        access_token = YOUR_COZE_TOKEN

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        data = {
            'conversation_id': self.conversation_id,
            'bot_id': self.bot_id,
            'user_id': self.user_id,
            'stream': True,
            'auto_save_history': True,
            'additional_messages': [
                {
                    'role': 'user',
                    'content': msg_to_coze,
                    'content_type': 'text'
                }
            ]
        }

        response = requests.post('https://api.coze.cn/v3/chat', headers=headers, json=data, stream=True)

        try:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('event:'):
                        event_type = decoded_line.split(':', 1)[1].strip()
                    elif decoded_line.startswith('data:'):
                        event_data = decoded_line.split(':', 1)[1].strip()
                        self.handle_event(event_type, event_data)
        except requests.exceptions.HTTPError as http_err:
            self.display_callback(f'HTTP error occurred: {http_err}')
        except json.JSONDecodeError:
            self.display_callback('JSON decode error: 响应不是有效的 JSON 格式')
            self.display_callback('响应内容:', response.text)
        except Exception as err:
            self.display_callback(f'Other error occurred: {err}')
        finally:
            self.is_processing = False

    def display_user_message(self, message):
        self.display_callback(f'用户: {message}', user=True)

    def handle_event(self, event_type, event_data):

        print(f'----->Event type: {event_type}')
        print(f'----->Event data: {event_data}')

        if event_type == 'conversation.chat.created':
            data = json.loads(event_data)
            #self.display_callback(f'对话已创建: {data}')
        elif event_type == 'conversation.chat.in_progress':
            data = json.loads(event_data)
            #self.display_callback(f'对话进行中: {data}')
        elif event_type == 'conversation.message.delta':

            data = json.loads(event_data)
            if data.get('role') == 'assistant':
                new_content = data.get('content', '')
                # 不处理流式内容

        elif event_type == 'conversation.message.completed':
            try:
                data = json.loads(event_data)
                if data.get('type') == 'tool_response':
                    tool_res_data = data.get('content')

                    try:
                        tool_res_data = json.loads(tool_res_data)

                        self.pic_url = tool_res_data['output']
                        self.display_callback(f'工具抽取: {self.pic_url}')
                    except Exception as e:
                        pass

                    
                    # self.display_callback(f'工具响应: {data.get("content")}')
                elif data.get('type') == 'function_call':
                    raw_data = data.get('content')
                    tool_msg = json.loads(raw_data)
                    tool_use = f'工具调用: {tool_msg["plugin_name"]}'
                    self.display_callback(tool_use)
                    self.tts.synthesize_and_play(tool_use)
                elif data.get('type') == 'answer':
                    ai_message = data.get('content')
                    self.display_callback(f'AI 消息: {data.get("content")}')
                    if not self.current_message.startswith("http"):
                        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 应该播放: {}'.format(ai_message))
                        self.tts.synthesize_and_play(ai_message)
            except Exception as e:
                #self.display_callback(f'JSON decode error: {e}')
                pass
        elif event_type == 'conversation.chat.completed':
            if self.current_message:
                self.messages.append({'role': 'assistant', 'content': self.current_message})

                self.current_message = ''
            data = json.loads(event_data)
            #self.display_callback(f'对话已完成: {data}')
        elif event_type == 'conversation.chat.failed':
            data = json.loads(event_data)
            self.display_callback(f'对话失败: {data}')
        else:
            #self.display_callback(f'未知事件类型: {event_type}')
            pass

    def create_empty_conversation(self):
        access_token = YOUR_COZE_TOKEN

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        data = {
            'bot_id': self.bot_id,
            'user_id': self.user_id
        }

        response = requests.post('https://api.coze.cn/v1/conversation/create', headers=headers, json=data)

        try:
            response.raise_for_status()
            res_data = response.json()
            if res_data.get('code') == 0:
                self.conversation_id = res_data['data']['id']
                self.messages.append({'role': 'system', 'content': f'空会话已创建，ID: {self.conversation_id}'})
            else:
                self.display_callback(f'创建空会话失败: {res_data.get("msg")}')
        except requests.exceptions.HTTPError as http_err:
            self.display_callback(f'HTTP error occurred: {http_err}')
        except json.JSONDecodeError:
            self.display_callback('JSON decode error: 响应不是有效的 JSON 格式')
            self.display_callback('响应内容:', response.text)
        except Exception as err:
            self.display_callback(f'Other error occurred: {err}')


class RealTimeSt:
    def __init__(self, display_callback):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.sr = None
        self.is_recording = False
        self.chat_bot = MyChatBot(display_callback)

    def start_recording(self):
        self.is_recording = True
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        self.sr = nls.NlsSpeechTranscriber(
            url=URL,
            token=TOKEN,
            appkey=APPKEY,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_start=self.on_start,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.sr.start(aformat="pcm",
                      enable_intermediate_result=True,
                      enable_punctuation_prediction=True,
                      enable_inverse_text_normalization=True)
        self.recording_thread = threading.Thread(target=self.process_stream)
        self.recording_thread.start()

    def process_stream(self):
        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.sr.send_audio(data)
            time.sleep(0.01)

    def stop_recording(self):
        self.is_recording = False
        self.recording_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.sr.stop()

    def on_sentence_begin(self, message, *args):
        pass

    def on_sentence_end(self, message, *args):
        data = json.loads(message)
        result_content = data['payload']['result']
        threading.Thread(target=self.process_ai_response, args=(result_content,)).start()

    def process_ai_response(self, result_content):
        self.chat_bot.input_value = result_content
        self.chat_bot.send_message()

    def on_start(self, message, *args):
        pass

    def on_result_changed(self, message, *args):
        pass

    def on_completed(self, message, *args):
        pass

    def on_error(self, message, *args):
        pass

    def on_close(self, *args):
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat Application")
        self.root.geometry("800x600")  # 固定窗口大小

        self.left_frame = ttk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.text_area = scrolledtext.ScrolledText(self.left_frame, wrap=tk.WORD, font=("Helvetica", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.display_area = tk.Label(self.right_frame)
        self.display_area.pack(fill=tk.BOTH, expand=True)

        self.realtime_st = RealTimeSt(self.display_message)

        self.recording = False
        self.toggle_button = ttk.Button(self.root, text="Start Recording", command=self.toggle_recording)
        self.toggle_button.pack(side=tk.BOTTOM)

        # 初始化锁
        self.lock = threading.Lock()

        # 用于存储消息的列表
        self.messages = []


        self.setup_styles()

    def toggle_recording(self):
        if self.recording:
            self.realtime_st.stop_recording()
            self.toggle_button.config(text="Start Recording")
        else:
            self.realtime_st.start_recording()
            self.toggle_button.config(text="Stop Recording")
        self.recording = not self.recording

    def display_message(self, message, user=False, stream=False, update=False):
        with self.lock:  # 使用锁来同步访问
            if user:
                # self.messages.append(f'用户: {message}')
                self.text_area.insert(tk.END, f'用户: {message}\n', 'user')
            elif stream:
                if update and self.messages and self.messages[-1].startswith('助手:'):
                    # 更新最后一个助手消息
                    self.messages[-1] = f'助手: {message}'
                    # 获取最后一行的起始索引
                    last_line_index = self.text_area.index('end-2l')
                    # 删除最后一行
                    self.text_area.delete(last_line_index, 'end-1l')
                    self.text_area.insert(tk.END, f'助手: {message}\n', 'assistant')
                else:
                    self.messages.append(f'助手: {message}')
                    self.text_area.insert(tk.END, f'助手: {message}\n', 'assistant')
            else:
                self.messages.append(message)
                self.text_area.insert(tk.END, f'{message}\n')
            self.text_area.yview(tk.END)

            if message.startswith("工具抽取:"):
                content = message.split("工具抽取:")[1].strip()
                if content.startswith("https"):
                    self.display_image(content)

    def display_image(self, url):
        try:
            image_bytes = urlopen(url).read()
            data_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(data_stream)
            tk_image = ImageTk.PhotoImage(pil_image)
            self.display_area.config(image=tk_image)
            self.display_area.image = tk_image
        except Exception as e:
            self.display_message(f"无法加载图片: {e}")

    def setup_styles(self):
        self.text_area.tag_configure('user', foreground='black', background='lightblue')
        self.text_area.tag_configure('assistant', foreground='black', background='white')

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()