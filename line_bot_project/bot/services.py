from linebot import LineBotApi
from linebot.models import FlexSendMessage
from django.conf import settings
import requests
import uuid
from datetime import datetime
import logging
from .models import UserTag

logger = logging.getLogger(__name__)

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
            logger.error(f"推送失敗: {str(e)}")
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


    def track_message_click(self, user_id, action):
        """追蹤訊息點擊"""
        try:
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

    def create_custom_flex_message(self, image_url, description, button1_label, button2_label):
        """創建自定義 Flex Message"""
        flex_message_json = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": image_url,
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
                        "text": description,
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
                    "style": "link",
                 
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "postback",
                            "label": button1_label,
                            "data": "action=button1"
                        }
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": button2_label,
                            "data": "action=button2"
                        }
                    }
                ]
            }
        }
        return FlexSendMessage(alt_text='互動訊息', contents=flex_message_json)

    def send_narrowcast_message(self, tag_name, flex_message=None):
        """發送針對性訊息並追蹤已讀狀態"""
        try:
            # 如果提供了自定義參數，使用 create_custom_flex_message
            if isinstance(flex_message, dict) and all(key in flex_message for key in ['image_url', 'description', 'button1_label', 'button2_label']):
                flex_message = self.create_custom_flex_message(
                    image_url=flex_message['image_url'],
                    description=flex_message['description'],
                    button1_label=flex_message['button1_label'],
                    button2_label=flex_message['button2_label']
                )
            elif flex_message is None:
                flex_message = self.create_flex_message()

            # 生成唯一的追蹤 ID
            tracking_id = str(uuid.uuid4())
            
            # 在發送訊息前，先記錄這個追蹤 ID
            UserTag.objects.create(
                user_id='system',
                tag_name=f'message_{tracking_id}',
                extra_data={'status': 'sent'}
            )

            # 從資料庫獲取目標用戶
            users = list(UserTag.objects.filter(
                tag_name=tag_name
            ).values_list('user_id', flat=True).distinct())

            if not users:
                logger.warning(f"找不到標籤 {tag_name} 的用戶")
                return {
                    'success': False,
                    'message': f'找不到標籤 {tag_name} 的用戶'
                }

            # 分批發送
            batch_size = 500
            success_count = 0
            failed_count = 0

            for i in range(0, len(users), batch_size):
                batch_users = users[i:i + batch_size]
                try:
                    self.line_bot_api.multicast(
                        to=batch_users,
                        messages=flex_message,
                        retry_key=tracking_id
                    )
                    success_count += len(batch_users)
                    
                    # 記錄發送成功的用戶
                    UserTag.objects.bulk_create([
                        UserTag(
                            user_id=user_id,
                            tag_name=f'message_sent_{tracking_id}',
                            extra_data={'status': 'delivered'}
                        ) for user_id in batch_users
                    ])
                        
                except Exception as e:
                    failed_count += len(batch_users)
                    logger.error(f"批次發送失敗: {str(e)}")
            logger.info(f"發送完成: 成功 {success_count} 人, 失敗 {failed_count} 人")
            return {
                'success': True,
                'tracking_id': tracking_id,
                'message': f'發送完成: 成功 {success_count} 人, 失敗 {failed_count} 人'
            }

        except Exception as e:
            logger.error(f"發送錯誤: {str(e)}")
            return {
                'success': False,
                'message': f'發送錯誤: {str(e)}'
            }
    def track_message_impression(self, user_id):
        """追蹤訊息已讀"""
        try:
            # 檢查是否有未標記已讀的訊息
            recent_messages = UserTag.objects.filter(
                user_id=user_id,
                tag_name__startswith='message_sent_',
                extra_data__status='delivered'
            ).order_by('-tagged_at')[:5]  # 只檢查最近的5條訊息

            for message in recent_messages:
                tracking_id = message.tag_name.split('message_sent_')[1]
                
                # 標記為已讀
                result = self.tag_user(
                    user_id=user_id,
                    tag_name=f'message_read_{tracking_id}'
                )
                
                # 更新訊息狀態
                message.extra_data['status'] = 'read'
                message.save()

                if result['success']:
                    return {
                        'success': True,
                        'tagged_at': result['tagged_at'],
                        'tracking_id': tracking_id,
                        'message': '已讀追蹤成功'
                    }

            return {
                'success': False,
                'tagged_at': None,
                'message': '沒有找到需要標記已讀的訊息'
            }

        except Exception as e:
            return {
                'success': False,
                'tagged_at': None,
                'message': str(e)
            }