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
        self._handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        
        @self._handler.add(FollowEvent)
        def handle_follow(event):
            """處理用戶加入好友事件"""
            # 發送歡迎訊息和 Flex Message
            self.line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text="感謝您加入！"),
                    self.line_service.create_flex_message()
                ]
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
            tag_name = f"clicked_{data.get('action')}"
            user_id = event.source.user_id
            
            # 記錄點擊標籤到資料庫
            result = self.line_service.tag_user(
                user_id,
                tag_name
            )
            
            # 回覆確認訊息
            if result['success']:
                reply_message = (
                    f"標籤添加成功！\n"
                    f"時間: {result['tagged_at']}\n"
                    f"用戶ID: {user_id}\n"
                    f"標籤: {tag_name}"
                )
            else:
                reply_message = (
                    f"標籤添加失敗\n"
                    f"用戶ID: {user_id}\n"
                    f"標籤: {tag_name}\n"
                    f"錯誤: {result['message']}"
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