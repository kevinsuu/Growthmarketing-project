from linebot import LineBotApi
from linebot.models import FlexSendMessage
from django.conf import settings
import requests
import uuid
from datetime import datetime
import logging
from .models import UserTag
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LineMessageService:
    def __init__(self):
        self.line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
        self.api_endpoint = "https://api.line.me/v2/bot/audienceGroup"
        self.headers = {
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        self.statistics_endpoint = "https://api.line.me/v2/bot/insight/message/event"

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
    def get_audience_group_count(self, audience_group_id):
        """獲取受眾群組的用戶數量"""
        try:
            url = f"{self.api_endpoint}/{audience_group_id}"
            response = requests.get(url, headers=self.headers)
            logger.info(f"Audience group count response code: {response.status_code}")
            if response.status_code == 200:
                group_info = response.json()
                logger.info(f"Audience group info: {group_info}")
                return group_info.get('audienceGroup', {}).get('audienceCount', 0)
            return 0
        except Exception as e:
            logger.error(f"獲取受眾群組數量失敗: {str(e)}")
            return 0
    def send_narrowcast_message(self, tag_name, flex_message=None):
        """使用 API 發送針對性訊息並追蹤已讀狀態"""
        try:
            # 處理 flex_message
            audience_group_id = flex_message['audience_group_id']
            audience_count = self.get_audience_group_count(audience_group_id)

            if isinstance(flex_message, dict) and all(key in flex_message for key in ['image_url', 'description', 'button1_label', 'button2_label']):
                flex_content = {
                    "type": "flex",
                    "altText": "互動訊息",
                    "contents": {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": flex_message['image_url'],
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
                                    "text": flex_message['description'],
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
                                        "label": flex_message['button1_label'],
                                        "data": "action=button1"
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "secondary",
                                    "action": {
                                        "type": "postback",
                                        "label": flex_message['button2_label'],
                                        "data": "action=button2"
                                    }
                                }
                            ]
                        }
                    }
                }
            else:
                # 使用預設的 flex message
                flex_content = {
                    "type": "flex",
                    "altText": "互動訊息",
                    "contents": self.create_flex_message().contents
                }
            


            # 準備 API 請求
            logger.info(f"Audience group ID: {audience_group_id}")
            url = "https://api.line.me/v2/bot/message/narrowcast"
            payload = {
                "messages": [flex_content],
                "recipient": {
                    "type": "operator",
                    "and": [
                        {
                            "type": "audience",
                            "audienceGroupId": audience_group_id
                        }
                    ]
                }
            }

            # 發送請求
            response = requests.post(
                url,
                headers=self.headers,
                json=payload
            )
            logger.info(f"Narrowcast response code: {response.status_code}")
            if response.status_code == 202:
                # 取得請求 ID
                logger.info(f"Narrowcast response headers: {response.headers}")
                request_id = response.headers.get('x-line-request-id', str(uuid.uuid4()))
                logger.info(f"Narrowcast 發送成功，Request ID: {request_id}")
                user_tag = UserTag.objects.create(
                    user_id=user_id,
                    tag_name=f'message_sent_{request_id}',
                    extra_data={'status': 'sent'}
                )
                return {
                    'success': True,
                    'request_id': request_id,
                    'message': f'訊息已發送給 {audience_count} 位用戶'
                }
            else:
                error_message = response.text if response.text else f"HTTP 狀態碼: {response.status_code}"
                logger.error(f"API 請求失敗: {error_message}")
                return {
                    'success': False,
                    'message': f'發送失敗: {error_message}'
                }


        except Exception as e:
            logger.error(f"發送錯誤: {str(e)}")
            return {
                'success': False,
                'message': f'發送錯誤: {str(e)}'
            }
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
            # 檢查是否有未標記已讀的訊息
            recent_messages = UserTag.objects.filter(
                user_id=user_id,
                tag_name__startswith='message_sent_',
                extra_data__status='delivered'
            ).order_by('-tagged_at')[:5]  # 只檢查最近的5條訊息

            for message in recent_messages:
                tracking_id = message.tag_name.split('message_sent_')[1]
                
                # 更新訊息狀態為已讀
                UserTag.update_message_status(tracking_id, user_id, 'read')
                
                # 記錄點擊動作
                result = self.tag_user(
                    user_id=user_id,
                    tag_name=f'clicked_{action}_{tracking_id}'
                )
                
                if result['success']:
                    return {
                        'success': True,
                        'tagged_at': result['tagged_at'],
                        'tracking_id': tracking_id,
                        'message': '點擊追蹤成功'
                    }

            return {
                'success': False,
                'tagged_at': None,
                'message': '沒有找到相關訊息'
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
    def get_message_statistics(self, tracking_id):
        """獲取訊息統計數據"""
        try:
            # 獲取發送記錄
       
            # 計算時間範圍（從發送時間到現在）
            today = datetime.now().date()
            logger.info(f"requestId{ tracking_id}")
            # 使用 Insight API 獲取訊息已讀數據
            insight_url = f"{self.statistics_endpoint}"
            params = {
                "requestId": tracking_id,
            }
            
            response = requests.get(
                insight_url,
                headers=self.headers,
                params=params
            )

            if response.status_code == 200:
                insight_data = response.json()
                read_count = insight_data.get("overview", {}).get("uniqueImpression", 0)

                if read_count == 0.0:
                    # 檢查按鈕點擊
                    button1_count = UserTag.objects.filter(
                        tag_name=f'clicked_button1_{tracking_id}'
                    ).count()
                    
                    button2_count = UserTag.objects.filter(
                        tag_name=f'clicked_button2_{tracking_id}'
                    ).count()
                    read_count = 1 if (button1_count > 0 or button2_count > 0) else 0.0
            else:
                logger.warning(f"無法從 Insight API 獲取數據: {response.text}")
                # 如果 API 失敗，使用資料庫的數據作為備用
                read_count = UserTag.objects.filter(
                    tag_name=f'message_read_{tracking_id}'
                ).count()

    

            # 計算總發送數
            total_sent = 0
            read_count = 0

            if response.status_code == 200:
                insight_data = response.json()
                total_sent = insight_data.get("overview", {}).get("delivered", 0) or 0
                read_count = insight_data.get("message", {}).get("impression", 0) or 0
                if total_sent == 0:
                    return {
                        'success': True,
                        'statistics': {
                            'tracking_id': tracking_id,
                            'message': '等待 LINE 更新數據中...',
                            'status': 'pending'
                        }
                    }
            else:
                logger.warning(f"無法從 Insight API 獲取數據: {response.text}")
                
            # 確保數值為整數並計算比率
            total_sent = int(total_sent)
            read_count = int(read_count)
            read_rate = (read_count / total_sent * 100) if total_sent > 0 else 0


            return {
                'success': True,
                'statistics': {
                    'tracking_id': tracking_id,
                    'total_sent': total_sent,
                    'read_count': read_count,
                    'read_rate': round(read_rate, 2),
                }
            }

        except Exception as e:
            logger.error(f"獲取統計數據失敗: {str(e)}")
            return {
                'success': False,
                'message': f'獲取統計數據失敗: {str(e)}'
            }