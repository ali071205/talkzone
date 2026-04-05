from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Setup TalkZone - make strawhatlufy superuser'

    def handle(self, *args, **options):
        # Make your account superuser on Render
        usernames = ['strawhatlufy', 'xorohunter']
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                if not user.is_superuser:
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Made {username} a superuser'))
                else:
                    self.stdout.write(f'{username} is already a superuser')
            except User.DoesNotExist:
                self.stdout.write(f'{username} not found, skipping')

        self.stdout.write(self.style.SUCCESS('TalkZone setup complete!'))
