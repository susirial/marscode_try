# PC 阿里语音识别测试
import pyaudio
import threading
import time
import nls
import json

from ali_env_setting import MY_ALI_APPKEY,MY_ALI_TOKEN
# ali_env_setting 是我本地的一个配置文件
ALI_TOKEN = MY_ALI_TOKEN
ALI_APPKEY = MY_ALI_APPKEY
# llms 定义了AI相关方法

#上海
#URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
#北京
URL ="wss://nls-gateway-cn-beijing.aliyuncs.com/ws/v1"
TOKEN = ALI_TOKEN # 参考https://help.aliyun.com/document_detail/450255.html获取token
APPKEY = ALI_APPKEY
#定义录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
class RealTimeSt:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.sr = None
        self.is_recording = False
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
        print("Recording started...")
        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.sr.send_audio(data)
            time.sleep(0.01)
        print("Recording stopped.")
    def stop_recording(self):
        self.is_recording = False
        self.recording_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.sr.stop()
        # 定义回调函数
    def on_sentence_begin(self, message, *args):
        print("Sentence begin: {}".format(message))
    def on_sentence_end(self, message, *args):
        #print("Sentence end: {}".format(message))
        # 将字符串转换为字典
        data = json.loads(message)
        result_content = data['payload']['result']
        print('on_sentence_end 阿里语音识别：{} \n'.format(result_content))
        # ai_talk 的细节需要自己实现
        #threading.Thread(target=ai_talk, args=(result_content,)).start()
    def on_start(self, message, *args):
        print("Start recognition: {}".format(message))
    def on_result_changed(self, message, *args):
        #print("Result changed: {}".format(message))
        # 将字符串转换为字典
        data = json.loads(message)
        result_content = data['payload']['result']
        print('on_result_changed 阿里语音识别：{} \n'.format(result_content))
    def on_completed(self, message, *args):
        print("Recognition completed: {}".format(message))
    def on_error(self, message, *args):
        print("Error occurred: {}".format(args))
    def on_close(self, *args):
        print("Connection closed: {}".format(args))
    # 使用示例

if __name__ == '__main__':
    realtime_st = RealTimeSt()
    realtime_st.start_recording()
    time.sleep(10)  # 录制120秒
    realtime_st.stop_recording()