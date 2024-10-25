from django.urls import path
from .views import (
    LineWebhookView, 
    RemoveRichMenuView,
    NarrowcastMessageView,
    TagStatsView,
    views
)
urlpatterns = [
    path('webhook/', LineWebhookView.as_view(), name='line_webhook'),
    path('remove-rich-menu/', RemoveRichMenuView.as_view(), name='remove_rich_menu'),
    path('narrowcast/', NarrowcastMessageView.as_view(), name='narrowcast'),
    path('web/', TagStatsView.as_view(), name='tag_stats'),  # 新的URL路徑
    path('push-message/', views.push_message, name='push_message'),

]
