from linebot import LineBotApi
from linebot.models import FlexSendMessage
from django.conf import settings
import requests
import uuid
from datetime import datetime

from .models import UserTag
class LineMessageService:
    def __init__(self):
        self.line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
  
    def create_flex_message(self):
        """創建 Flex Message"""
        flex_message_json = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "文字描述",
                        "wrap": True,
                        "weight": "bold",
                        "size": "xl"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "postback",
                            "label": "按鈕 1",
                            "data": "action=button1"
                        }
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "按鈕 2",
                            "data": "action=button2"
                        }
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text='互動訊息', contents=flex_message_json)

    def tag_user(self, user_id, tag_name):
        """為用戶添加標籤"""
        try:
            # 只記錄到資料庫
            user_tag = UserTag.objects.create(
                user_id=user_id,
                tag_name=tag_name
            )
            return {
                'success': True,
                'message': f'標籤已新增: {tag_name}',
                'tagged_at': user_tag.tagged_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'標籤新增失敗: {str(e)}'
            }
    def push_flex_message_to_user(self, user_id):
        """主動推送 Flex Message 給用戶"""
        try:
            flex_message = self.create_flex_message()
            self.line_bot_api.push_message(user_id, flex_message)
            return True
        except Exception as e:
            print(f"推送失敗: {str(e)}")
            return False
