# Import necessary libraries
import pyperclip
import threading
import time
import asyncio
import websockets
import json
from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

# Initialize controllers
keyboard_controller = KeyboardController()
mouse_controller = MouseController()

# Global variable to store WebSocket clients
clients = set()

# Function to broadcast messages to all connected WebSocket clients
async def broadcast(message):
    if clients:
        await asyncio.gather(*[client.send(message) for client in clients])

# WebSocket server handler
async def handler(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            # Process incoming messages from Electron
            data = json.loads(message)
            print(f"Received message from Electron: {data}")
            # You can add custom processing logic here
    finally:
        clients.remove(websocket)

# Start WebSocket server
def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(handler, 'localhost', 8765)
    loop.run_until_complete(server)
    loop.run_forever()

# Function to monitor combination of "cmd c c"
def monitor_keyboard():

    # The key combination to check
    # 新定义快捷键组合 or 相对原有逻辑有变动的组合键
    HotKeys = {
        "cmd+c+c": [keyboard.Key.cmd, keyboard.KeyCode.from_char('c'), keyboard.KeyCode.from_char('c')],
        "cmd+c": [keyboard.Key.cmd, keyboard.KeyCode.from_char('c')],
        "cmd+x": [keyboard.Key.cmd, keyboard.KeyCode.from_char('x')]
    }

    # The currently active modifiers
    current = [{
        "key": Key.space,
        "time": time.time()
    }]
    clipboard_content = [""]
    clipboard_content_str = ""

    # 启动时清空剪贴板
    pyperclip.copy("")

    def on_press(key):
        nonlocal current, clipboard_content, clipboard_content_str

        # current 最多记录最近按下的三个键及其时间
        current.append({
            "key": key,
            "time": time.time()
        })
        current = current[-3:]

    def on_release(key):
        nonlocal current, clipboard_content, clipboard_content_str

        # cmd 键释放，代表 cmd 相关快捷键的结束
        if key == Key.cmd:
            # print(key, current)
            # **增量复制**：如果最近按下 cmd c c，且 cmd 和 最后一个 c 键时间间隔不超过 0.5s
            # 增加最新剪贴板内容到剪贴板历史
            # 拼接剪贴板历史并更新剪贴板
            if [item["key"] for item in current] == HotKeys['cmd+c+c'] and current[-1]["time"] - current[0]["time"] < 0.5:
                time.sleep(0.1) # 预留系统读取剪贴板时间
                clipboard_content.append(pyperclip.paste()) # 获取最新剪贴板内容
                clipboard_content_str = '\n'.join(clipboard_content)
                pyperclip.copy(clipboard_content_str)
                print("增量复制：\n", clipboard_content_str)
                message = json.dumps({'type': 'keyboard', 'key': 'cmd+c+c', 'content': clipboard_content_str})
                asyncio.run(broadcast(message))
            
            # **普通复制**：仅按下 cmd c
            # 覆盖剪贴板历史为当前剪贴板内容，意为清空增量复制结果
            if [item["key"] for item in current[-2:]] == HotKeys['cmd+c'] and current[-1]["time"] - current[-2]["time"] < 0.5:
                time.sleep(0.1)
                clipboard_content_str = pyperclip.paste()
                clipboard_content = [clipboard_content_str]
                print("复制：\n", clipboard_content_str)
            
            # **剪切**：按下 cmd x
            # 覆盖剪贴板历史为当前剪贴板内容，意为清空增量复制结果
            if [item["key"] for item in current[-2:]] == HotKeys['cmd+x'] and current[-1]["time"] - current[-2]["time"] < 0.5:
                time.sleep(0.1)
                clipboard_content_str = pyperclip.paste()
                clipboard_content = [clipboard_content_str]
                print("剪切：\n", clipboard_content_str)

            # 按下 cmd 立即释放，添加一个防御性 字符，帮助鉴别各种操作
            if current[-1]["key"] == Key.cmd:
                current.append({
                    "key": Key.space,
                    "time": time.time()
                })      

    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    keyboard_listener.start()

    
    while True:
        tmp_value = pyperclip.paste()

        # 每 500ms 检测一次剪贴板是否变化
        # 检测到的复制内容不是剪贴板历史最后一个，也不是增量复制覆盖剪贴板的内容
        # 那么是鼠标操作的复制添加到剪贴板的
        if tmp_value not in [clipboard_content[-1], clipboard_content_str]:
                
                # **鼠标 + cmd 复制**：剪贴板检测到新内容，且最新按键是 cmd
                # 添加最新剪贴版内容到剪贴板历史
                # 拼接剪贴板历史并更新剪贴板
                # 上方释放 cmd 键后，为 current 添加防御性按键 space，帮助区分“鼠标复制”
                if current[-1]["key"] == keyboard.Key.cmd:
                    clipboard_content.append(tmp_value)
                    clipboard_content_str = "\n".join(clipboard_content)
                    pyperclip.copy(clipboard_content_str)
                    print("鼠标 + cmd 增量复制\n", clipboard_content_str)
                    message = json.dumps({'type': 'clipboard', 'content': clipboard_content_str, 'key': 'option'})
                    asyncio.run(broadcast(message))

                # **鼠标复制**：剪贴板检测到新内容，且不是 cmd c、cmd c c、cmd x、鼠标 + cmd 中的任意一种
                # 覆盖剪贴板历史为当前剪贴板内容，意为清空增量复制结果
                # print(current)
                if len(current)>=3 and current[-1]["key"]!= keyboard.Key.cmd \
                    and [item["key"] for item in current[-2:]]!= HotKeys['cmd+c'] \
                    and [item["key"] for item in current] != HotKeys['cmd+c+c'] \
                    and [item["key"] for item in current[-2:]]!= HotKeys['cmd+x']:
                    clipboard_content_str = tmp_value
                    clipboard_content = [clipboard_content_str]
                    print("鼠标复制1：\n", clipboard_content_str)
                    message = json.dumps({'type': 'clipboard', 'content': clipboard_content_str, 'key': 'option'})
                    asyncio.run(broadcast(message))

                # **鼠标复制**：剪贴板检测到新内容，初始情况下，直接用鼠标复制了一个内容
                if len(current) == 1 and current[-1]["key"] != keyboard.Key.cmd:
                    clipboard_content_str = tmp_value
                    clipboard_content = [clipboard_content_str]
                    print("鼠标复制2：\n", clipboard_content_str)
                    message = json.dumps({'type': 'clipboard', 'content': clipboard_content_str, 'key': 'option'})
                    asyncio.run(broadcast(message))
            
        time.sleep(0.5)

# Start keyboard monitoring in a separate thread
keyboard_thread = threading.Thread(target=monitor_keyboard)
keyboard_thread.start()

# Start WebSocket server in a separate thread
websocket_thread = threading.Thread(target=start_websocket_server)
websocket_thread.start()

# Keep the main thread running
keyboard_thread.join()
# clipboard_thread.join()
websocket_thread.join()
