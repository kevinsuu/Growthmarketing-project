from django.core.management.base import BaseCommand
from bot.services import LineMessageService

class Command(BaseCommand):
    help = '向指定用戶推送 Flex Message'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str)

    def handle(self, *args, **options):
        service = LineMessageService()
        user_id = options['user_id']
        if service.push_flex_message_to_user(user_id):
            self.stdout.write(self.style.SUCCESS(f'成功推送給用戶 {user_id}'))
        else:
            self.stdout.write(self.style.ERROR(f'推送失敗 {user_id}'))