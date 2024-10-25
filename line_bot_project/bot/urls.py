from django.urls import path
from .views import (
    LineWebhookView, 
    RemoveRichMenuView,
    NarrowcastMessageView  # 確保這個視圖被導入
)
urlpatterns = [
    path('webhook/', LineWebhookView.as_view(), name='line_webhook'),
    path('remove-rich-menu/', RemoveRichMenuView.as_view(), name='remove_rich_menu'),
    path('narrowcast/', NarrowcastMessageView.as_view(), name='narrowcast'),

]
