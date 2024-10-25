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
        self.api_endpoint = "https://api.line.me/v2/bot/audienceGroup"
        self.headers = {
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
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
                'message': f'標籤新增失敗: {str(e)}',
                'tagged_at': None
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
    def create_audience_group(self, description):
        """創建受眾群組"""
        url = f"{self.api_endpoint}/create"
        payload = {
            "description": description,
            "isIfaAudience": False
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json().get('audienceGroupId')
        return None

    def add_audience(self, group_id, user_id):
        """添加用戶到受眾群組"""
        url = f"{self.api_endpoint}/{group_id}/users/add"
        payload = {
            "userIds": [user_id]
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.status_code == 200

    def track_message_impression(self, user_id):
        """追蹤訊息已讀"""
        try:
            # 直接記錄到資料庫，不再依賴 LINE API 的回應
            result = self.tag_user(user_id, 'message_impression')
            if result['success']:
                return {
                    'success': True,
                    'tagged_at': result['tagged_at'],
                    'message': '已讀追蹤成功'
                }
            return {
                'success': False,
                'tagged_at': None,
                'message': '已讀追蹤失敗'
            }
        except Exception as e:
            return {
                'success': False,
                'tagged_at': None,
                'message': str(e)
            }

    def track_message_click(self, user_id, action):
        """追蹤訊息點擊"""
        try:
            # 直接記錄到資料庫，不再依賴 LINE API 的回應
            result = self.tag_user(user_id, f'clicked_{action}')
            if result['success']:
                return {
                    'success': True,
                    'tagged_at': result['tagged_at'],
                    'message': '點擊追蹤成功'
                }
            return {
                'success': False,
                'tagged_at': None,
                'message': '點擊追蹤失敗'
            }
        except Exception as e:
            return {
                'success': False,
                'tagged_at': None,
                'message': str(e)
            }