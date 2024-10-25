from django.urls import path
from .views import LineWebhookView, RemoveRichMenuView

urlpatterns = [
    path('webhook/', LineWebhookView.as_view(), name='line_webhook'),
    path('remove-rich-menu/', RemoveRichMenuView.as_view(), name='remove_rich_menu'),
]
