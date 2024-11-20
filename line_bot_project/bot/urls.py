from django.urls import path
from .views import (
    LineWebhookView, 
    RemoveRichMenuView,
    NarrowcastMessageView,
    TagStatsView,
    PushMessageView,
    TrackMessageReadView
)

urlpatterns = [
    path('webhook/', LineWebhookView.as_view(), name='line_webhook'),
    path('remove-rich-menu/', RemoveRichMenuView.as_view(), name='remove_rich_menu'),
    path('narrowcast/', NarrowcastMessageView.as_view(), name='narrowcast'),
    path('web/', TagStatsView.as_view(), name='tag_stats'),  # 新的URL路徑
    path('api/push-message/', PushMessageView.as_view(), name='push_message'),
    path('track-read/<str:message_id>/', TrackMessageReadView.as_view(), name='track_read'),
]
