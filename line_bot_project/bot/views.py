from django.views import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, PostbackEvent, TextSendMessage, 
    FollowEvent, UnfollowEvent
)
from django.conf import settings
from .services import LineMessageService
from urllib.parse import parse_qsl
from django.views import View
from django.shortcuts import render
from .models import UserTag
      
@method_decorator(csrf_exempt, name='dispatch')
class LineWebhookView(View):
    def __init__(self):
        super().__init__()
        self.line_service = LineMessageService()
        self.line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
        self._handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        self.setup_handler()

    def setup_handler(self):
        @self._handler.add(MessageEvent)
        def handle_message(event):
            """處理收到訊息事件"""
            user_id = event.source.user_id
            
            # 追蹤訊息已讀
            impression_result = self.line_service.track_message_impression(user_id)
            
            if event.message.text.lower() == "start":
                # 發送 Flex Message
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self.line_service.create_flex_message()
                )
            else:
                # 回覆已讀確認訊息
                reply_message = (
                    f"訊息已讀！\n"
                    f"時間: {impression_result['tagged_at']}\n"
                    f"用戶ID: {user_id}\n"
                    f"標籤: message_impression"
                )
                
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_message)
                )
                
        @self._handler.add(PostbackEvent)
        def handle_postback(event):
            data = dict(parse_qsl(event.postback.data))
            action = data.get('action')
            user_id = event.source.user_id
            
            # 追蹤按鈕點擊
            click_result = self.line_service.track_message_click(user_id, action)
            
            if click_result['success']:
                reply_message = (
                    f"點擊活動成功\n"
                    f"追蹤ID: {click_result.get('tracking_id', 'N/A')}\n"
                    f"時間: {click_result['tagged_at']}\n"
                    f"用戶ID: {user_id}\n"
                    f"動作: {action}"
                )
            else:
                reply_message = (
                    f"點擊活動失敗\n"
                    f"用戶ID: {user_id}\n"
                    f"動作: {action}\n"
                    f"錯誤: {click_result['message']}"
                )
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_message)
            )

    def post(self, request, *args, **kwargs):
        signature = request.headers.get('X-Line-Signature', '')
        body = request.body.decode('utf-8')
        
        try:
            self._handler.handle(body, signature)
            return HttpResponse(status=200)
        except InvalidSignatureError:
            return HttpResponse(status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return HttpResponse(status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RemoveRichMenuView(View):
    def post(self, request, *args, **kwargs):
        try:
            line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
            line_bot_api.unlink_rich_menu_from_user('all')
            return JsonResponse({'status': 'success', 'message': 'Rich menu removed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

@method_decorator(csrf_exempt, name='dispatch')
class NarrowcastMessageView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            print(f"收到的請求數據: {data}")  # 添加調試信息
            
            tag_name = data.get('tag_name')
            image_url = data.get('image_url')
            description = data.get('description')
            button1_label = data.get('button1_label')
            button2_label = data.get('button2_label')

            if not all([tag_name, image_url, description, button1_label, button2_label]):
                return JsonResponse({
                    'success': False,
                    'message': '缺少必要參數'
                })

            line_service = LineMessageService()
            
            # 創建自定義 Flex Message
            flex_message = line_service.create_custom_flex_message(
                image_url=image_url,
                description=description,
                button1_label=button1_label,
                button2_label=button2_label
            )
            
            # 發送 narrowcast 訊息
            result = line_service.send_narrowcast_message(tag_name, flex_message)
            print(f"發送結果: {result}")  # 添加調試信息

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '無效的 JSON 格式'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
class TagStatsView(View):
    def get(self, request):
        stats, graph = UserTag.get_daily_tag_stats()
        context = {
            'stats': stats,
            'graph': graph
        }
        return render(request, 'bot/tag_stats.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class PushMessageView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'message': '缺少用戶ID'
                })

            line_service = LineMessageService()
            result = line_service.push_flex_message_to_user(user_id)
            
            if result:
                return JsonResponse({
                    'success': True,
                    'message': f'成功推送消息給用戶 {user_id}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'推送消息失敗'
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '無效的 JSON 格式'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })