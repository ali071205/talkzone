from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from a_rtchat.models import ChatGroup


class Command(BaseCommand):
    help = 'TalkZone initial setup - admin aur public chat banao'

    def handle(self, *args, **kwargs):
        # Admin user banao
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@talkzone.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('✅ Admin user bana!'))
        else:
            self.stdout.write('ℹ️  Admin pehle se hai!')

        # Public chat banao
        chat, created = ChatGroup.objects.get_or_create(
            group_name='public-chat',
            defaults={
                'groupchat_name': 'Public Chat',
                'is_private': False,
            }
        )
        if created:
            admin = User.objects.get(username='admin')
            chat.members.add(admin)
            self.stdout.write(self.style.SUCCESS('✅ Public chat bani!'))
        else:
            self.stdout.write('ℹ️  Public chat pehle se thi!')

        self.stdout.write(self.style.SUCCESS('🎉 TalkZone setup complete!'))