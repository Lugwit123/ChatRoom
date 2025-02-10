from enum import Enum

class MessageContentType(str, Enum):
    """消息内容类型枚举"""
    rich_text = 'rich_text'  # 富文本消息
    url = 'url'              # 超链接
    audio = 'audio'          # 音频
    image = 'image'          # 图片
    video = 'video'          # 视频
    file = 'file'            # 文件
    plain_text = 'plain_text' # 纯文本
    user_list = 'user_list'
    html = 'html'

# 迭代获取所有键和值
for key, value in MessageContentType.__members__.items():
    print(f"Key: {key}, Value: {value.value}")
