from django.views import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, PostbackEvent, TextSendMessage, 
    FollowEvent, UnfollowEvent
)
from django.conf import settings
from .services import LineMessageService
from urllib.parse import parse_qsl

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

        @self._handler.add(MessageEvent)
        def handle_message(event):
            """處理收到訊息事件"""
            user_id = event.source.user_id
            
            # 記錄已讀標籤到資料庫
            result = self.line_service.tag_user(
                user_id,
                'message_read'
            )
            print(f"已讀標籤結果: {result}")

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
                    f"時間: {result['tagged_at']}\n"
                    f"用戶ID: {user_id}\n"
                    f"標籤: message_read"
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