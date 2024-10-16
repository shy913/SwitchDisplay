import pyaudio
import threading
import cv2
import time
import numpy as np

# 全局退出标志
exit_flag = False


# 声音捕获和播放线程函数
def audio_stream(input_device_index):
    global exit_flag
    p = pyaudio.PyAudio()

    # 打开输入流 (从采集卡获取音频)
    input_stream = p.open(format=pyaudio.paInt16,  # 16位音频格式
                          channels=2,  # 立体声
                          rate=44100,  # 采样率
                          input=True,  # 设置为输入设备
                          input_device_index=input_device_index,  # 采集卡音频设备索引
                          frames_per_buffer=1024)  # 每次读入1024帧

    # 打开输出流 (播放音频)
    output_stream = p.open(format=pyaudio.paInt16,  # 16位音频格式
                           channels=2,  # 立体声
                           rate=44100,  # 采样率
                           output=True,  # 设置为输出设备
                           frames_per_buffer=1024)  # 每次写入1024帧


    try:
        while not exit_flag:  # 在退出标志为 False 时持续运行
            # 从输入流读取音频数据
            data = input_stream.read(1024)
            # 将音频数据写入输出流，播放音频
            output_stream.write(data)
    except IOError as e:
        print(f"音频流出错: {e}")

    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    p.terminate()

def capture_frame(cap):
    global frame, ret, exit_flag
    while not exit_flag:  # 在退出标志为 False 时持续运行
        ret, frame = cap.read()
        if not ret or exit_flag:
            break


def interpolate_frame(prev, next):
    # Calculate the time to display each frame to simulate 120 fps
    display_time = 1 / 120  # seconds per frame

    # Convert images to float for precision
    prev_float = prev.astype(np.float32)
    next_float = next.astype(np.float32)

    # Compute the middle frame by averaging the previous and next frames
    mid = 0.5 * (prev_float + next_float)

    # Convert back to unsigned 8-bit integer
    mid = np.clip(mid, 0, 255).astype(np.uint8)

    # Display the previous and middle frames
    cv2.imshow('Previous', prev)
    start_time = time.time()
    # Ensure the frame is displayed for approximately half the time
    # (to fit two frames within the period originally for one)
    while time.time() - start_time < display_time:
        cv2.waitKey(1)

    cv2.imshow('Middle', mid)
    start_time = time.time()
    while time.time() - start_time < display_time:
        cv2.waitKey(1)

    cv2.imshow('Next', next)
    start_time = time.time()
    while time.time() - start_time < display_time:
        cv2.waitKey(1)

    # Close all OpenCV windows
    cv2.destroyAllWindows()

def show_frame(frame):
    if frame is None:
        return  # 如果帧是None，则不进行处理

    global exit_flag
    if exit_flag:
        return
    # 获取帧的宽高
    frame_height, frame_width = frame.shape[:2]

    # 计算缩放比例，保持宽高比
    scale = min(my_screen_width / frame_width, my_screen_height / frame_height)
    new_width = int(frame_width * scale)
    new_height = int(frame_height * scale)

    # 等比例缩放画面
    resized_frame = cv2.resize(frame, (new_width, new_height))

    # 创建黑色背景画布
    canvas = cv2.copyMakeBorder(
        resized_frame,
        top=(my_screen_height - new_height) // 2,
        bottom=(my_screen_height - new_height) // 2,
        left=(my_screen_width - new_width) // 2,
        right=(my_screen_width - new_width) // 2,
        borderType=cv2.BORDER_CONSTANT,
        value=[0,0,0]  # 黑色背景
    )

    # 显示居中的画面
    cv2.imshow('Switch Capture', canvas)

def list_audio_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"设备索引: {i}, 设备名称: {info['name']}")
    p.terminate()


# 列出音频设备，找到你的采集卡设备索引
# 设置视频捕捉设备的索引
# list_audio_devices()
# audio_device_index = int(input("请输入采集卡音频设备的索引: "))
audio_device_index = 1
capture_device_index = 0
print('尝试打开采集卡')
cap = cv2.VideoCapture(capture_device_index)
# 检查采集卡是否成功打开
if not cap.isOpened():
    print("无法打开采集卡设备")
    exit()
print('成功打开采集卡')
# 设置捕获分辨率
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 45)
# 获取屏幕的分辨率，便于保持原比例
my_screen_width = 2560
my_screen_height = 1600
print('分辨率设置成功')


# 启动视频捕获线程
ret, frame = None, None
capture_thread = threading.Thread(target=capture_frame, args=(cap,))
capture_thread.start()
print('视频线程启动')

# 启动音频捕获和播放线程
# audio_thread = threading.Thread(target=audio_stream, args=(audio_device_index,))
# audio_thread.start()
# print('音频线程启动')

# 创建一个窗口并设置为全屏模式
cv2.namedWindow('Switch Capture', cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty('Switch Capture', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
print('窗口设置完成\n主线程启动')

# 显示画面的主线程
while True:
    if ret:
        show_frame(frame)
        # cv2.imshow('Switch Capture', frame)
    # 按 'Esc' 退出 (按键码27)
    if cv2.waitKey(5) & 0xFF == 27:
        print('正在退出')
        exit_flag = True  # 设置退出标志为 True，停止所有循环
        break

# 释放视频捕捉对象
print('释放视频捕捉对象')
cap.release()
cv2.destroyAllWindows()

# 等待音频和视频线程结束
print('等待音频和视频线程结束')
# audio_thread.join()
capture_thread.join()

print("所有进程已终止")
