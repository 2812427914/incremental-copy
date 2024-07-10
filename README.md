# 增量复制工具(incremental-copy) 

[English Version](./README_en.md)

**增量复制内容到剪贴板**：避免来回切换窗口，提高效率；

**websocket 广播事件**：方便集成该能力到其他项目中；

## 安装&启动
```
git clone https://github.com/2812427914/incremental-copy
cd incremental-copy
pip install -r requirements.txt
python main.py
```

## 使用
**cmd + c**：清空剪贴板历史并复制当前内容；

**鼠标右键复制**：复制当前内容并清空剪贴板历史；

**cmd + x**：清空剪贴板历史并剪贴当前内容；

**cmd + c + c：增量复制当前内容到剪贴板**；

**cmd + 鼠标右键复制：增量复制当前内容到剪贴板**；