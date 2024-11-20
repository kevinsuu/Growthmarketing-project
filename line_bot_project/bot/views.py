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
import logging

logger = logging.getLogger(__name__)
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
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self.line_service.create_flex_message()
                )
            else:
              
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
            click_result = self.line_service.track_message_click(user_id, action)
            
            if click_result['success']:
                reply_message = (
                    f"操作記錄成功！\n"
                    f"時間: {click_result['tagged_at']}\n"
                    f"用戶ID: {user_id}\n"
                    f"動作: {action}"
                )
            else:
                reply_message = (
                    f"操作記錄失敗\n"
                    f"用戶ID: {user_id}\n"
                    f"動作: {action}\n"
                    f"錯誤: {click_result['message']}"
                )
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_message)
            )

        # 處理已讀事件
        @self._handler.add(MessageEvent)
        def handle_read(event):
            user_id = event.source.user_id
            try:
                # 發送已讀確認訊息
                logger.info(f"使用者 {user_id} 已讀訊息")

                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text="訊息已讀！")
                )
            except LineBotApiError as e:
                logger.error(f"處理已讀事件時發生錯誤: {str(e)}")

    def post(self, request, *args, **kwargs):
        signature = request.headers.get('X-Line-Signature', '')
        body = request.body.decode('utf-8')
        
        try:
            self._handler.handle(body, signature)
            return HttpResponse(status=200)
        except InvalidSignatureError:
            return HttpResponse(status=400)
        except Exception as e:
            logger.info(f"Error: {str(e)}")
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
            user_id = data.get('user_id')
            message_type = data.get('message_type', 'text')
            
            line_service = LineMessageService()
            
            # 建立訊息
            if message_type == 'flex':
                message = line_service.create_flex_message()
            else:
                message = TextSendMessage(text="這是一條測試訊息")
            
            # 發送訊息並追蹤
            result = line_service.send_message_and_track_read(user_id, message)
            
            if result['success']:
                # 等待一段時間後檢查訊息狀態
                time.sleep(5)  # 等待 5 秒
                status = line_service.track_message_status(result['request_id'])
                
                return JsonResponse({
                    'success': True,
                    'message': '訊息發送成功',
                    'delivery_status': status
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f"發送失敗: {result.get('error')}"
                })
                
        except Exception as e:
            logger.error(f"處理請求時發生錯誤: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

# 新增一個檢查訊息狀態的端點
@method_decorator(csrf_exempt, name='dispatch')
class MessageStatusView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            
            if not request_id:
                return JsonResponse({
                    'success': False,
                    'message': '缺少 request_id'
                })
                
            line_service = LineMessageService()
            status = line_service.track_message_status(request_id)
            
            return JsonResponse({
                'success': True,
                'status': status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })class TagStatsView(View):
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