from linebot.models import (
    FlexSendMessage,
    NarrowcastRequest,
    MessageFilter,
    Filter
)
import time

class LineMessageService:
    def send_message_and_track_read(self, user_id, message):
        try:
            # 發送訊息
            response = self.line_bot_api.push_message(
                user_id,
                message,
                notification_disabled=False,
                custom_aggregation_units=["message_read"]  # 啟用訊息追蹤
            )
            
            # 取得訊息 request ID
            request_id = response.request_id
            
            # 追蹤訊息狀態
            return self.track_message_status(request_id)
            
        except LineBotApiError as e:
            logger.error(f"發送訊息失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def track_message_status(self, request_id):
        try:
            # 等待一段時間讓訊息送達
            time.sleep(2)
            
            # 獲取訊息發送狀態
            response = self.line_bot_api.get_message_delivery_status(request_id)
            
            return {
                'success': True,
                'request_id': request_id,
                'status': response.status,
                'delivered': response.delivered,
                'read': response.read,
                'undelivered': response.undelivered
            }
            
        except LineBotApiError as e:
            logger.error(f"獲取訊息狀態失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_narrowcast_message(self, message, filter_criteria=None):
        try:
            # 建立 narrowcast 請求
            request = NarrowcastRequest(
                messages=[message],
                filter=filter_criteria if filter_criteria else None,
                limit=1000  # 設定接收人數上限
            )
            
            # 發送 narrowcast
            response = self.line_bot_api.narrowcast(
                request,
                timeout=30  # 設定超時時間
            )
            
            return {
                'success': True,
                'request_id': response.request_id
            }
            
        except LineBotApiError as e:
            logger.error(f"Narrowcast 發送失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }