import requests
import json
import uuid

from coze_env_setting import MY_BOT_ID, MY_COZE_TOKEN

YOUR_BOT_ID = MY_BOT_ID
YOUR_COZE_TOKEN = MY_COZE_TOKEN

class ChatBot:
    def __init__(self):
        self.messages = []
        self.input_value = ''
        self.conversation_id = None
        self.bot_id = YOUR_BOT_ID  # 确保 bot_id 是一个有效的整数
        self.user_id = self.generate_uuid()  # 初始化 user_id

    def generate_uuid(self):
        return str(uuid.uuid4())

    def send_message(self):
        message = self.input_value
        if not message:
            return

        # 检查 conversation_id 是否为 None
        if not self.conversation_id:
            # 如果是 None，先创建一个新的会话
            self.create_empty_conversation(self.send_message)
            return

        # 添加用户消息到消息列表
        self.messages.append({'role': 'user', 'content': message})
        self.input_value = ''

        access_token = YOUR_COZE_TOKEN # 确保使用正确的访问令牌

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        data = {
            'conversation_id': self.conversation_id,  # 可选参数
            'bot_id': self.bot_id,
            'user_id': self.user_id,
            'stream': True,  # 启用流式返回
            'auto_save_history': True,
            'additional_messages': [
                {
                    'role': 'user',
                    'content': message,
                    'content_type': 'text'
                }
            ]
        }

        response = requests.post('https://api.coze.cn/v3/chat', headers=headers, json=data, stream=True)

        try:
            response.raise_for_status()  # 检查请求是否成功
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('event:'):
                        event_type = decoded_line.split(':', 1)[1].strip()
                    elif decoded_line.startswith('data:'):
                        event_data = decoded_line.split(':', 1)[1].strip()
                        self.handle_event(event_type, event_data)
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except json.JSONDecodeError:
            print('JSON decode error: 响应不是有效的 JSON 格式')
            print('响应内容:', response.text)
        except Exception as err:
            print(f'Other error occurred: {err}')

    def handle_event(self, event_type, event_data):
        # 处理不同类型的事件
        if event_type == 'conversation.chat.created':
            data = json.loads(event_data)
            print('对话已创建:', data)
        elif event_type == 'conversation.chat.in_progress':
            data = json.loads(event_data)
            print('对话进行中:', data)
        elif event_type == 'conversation.message.delta':
            data = json.loads(event_data)
            if data.get('role') == 'assistant':
                self.messages.append({'role': 'assistant', 'content': data.get('content')})
                print('助手消息:', data.get('content'))
        elif event_type == 'conversation.chat.completed':
            data = json.loads(event_data)
            print('对话已完成:', data)
        elif event_type == 'conversation.chat.failed':
            data = json.loads(event_data)
            print('对话失败:', data)
        else:
            print('未知事件类型:', event_type)

    def create_empty_conversation(self, callback):
        access_token = YOUR_COZE_TOKEN  # 确保使用正确的访问令牌

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
            response.raise_for_status()  # 检查请求是否成功
            res_data = response.json()
            if res_data.get('code') == 0:
                self.conversation_id = res_data['data']['id']
                self.messages.append({'role': 'system', 'content': f'空会话已创建，ID: {self.conversation_id}'})
                if callback:
                    callback()  # 执行回调函数
            else:
                print('创建空会话失败:', res_data.get('msg'))
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except json.JSONDecodeError:
            print('JSON decode error: 响应不是有效的 JSON 格式')
            print('响应内容:', response.text)
        except Exception as err:
            print(f'Other error occurred: {err}')

if __name__ == '__main__':

    # 使用示例
    chat_bot = ChatBot()
    chat_bot.input_value = "你好，你是谁？"
    chat_bot.send_message()
    pass