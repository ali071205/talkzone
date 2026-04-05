from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile, FriendRequest


@receiver(post_save, sender=User)
def user_postsave(sender, instance, created, **kwargs):
    user = instance
    if created:
        Profile.objects.create(user=user)
    else:
        try:
            email_address = EmailAddress.objects.get_primary(user)
            if email_address.email != user.email:
                email_address.email = user.email
                email_address.verified = False
                email_address.save()
        except:
            EmailAddress.objects.create(
                user=user, email=user.email,
                primary=True, verified=False
            )


@receiver(pre_save, sender=User)
def user_presave(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.lower()


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    name = user.profile.name if hasattr(user, 'profile') else user.username
    messages.success(request, f'✅ You have successfully logged in to TalkZone, {name}!')

    # Save login IP
    if hasattr(user, 'profile'):
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '')
        if ip:
            user.profile.last_login_ip = ip
            user.profile.save(update_fields=['last_login_ip'])

    # Kick other sessions
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    current = request.session.session_key
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            if session.session_key != current:
                session.delete()

    # Email notification
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject='✅ TalkZone Login Successful',
            message=f'Hi {name},\n\nYou have successfully logged in to TalkZone.\n\nIf this was not you, please change your password immediately.\n\n— TalkZone Team',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass


@receiver(post_save, sender=FriendRequest)
def friend_request_notification(sender, instance, created, **kwargs):
    """Email jab friend request aaye"""
    if created:
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            receiver = instance.receiver
            sender_user = instance.sender
            name = sender_user.profile.name if hasattr(sender_user, 'profile') else sender_user.username
            send_mail(
                subject=f'👥 {name} sent you a friend request on TalkZone',
                message=f'Hi {receiver.profile.name},\n\n{name} (@{sender_user.username}) sent you a friend request on TalkZone!\n\nLogin to accept or decline: http://127.0.0.1:8000/profile/friend-requests/\n\n— TalkZone Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[receiver.email],
                fail_silently=True,
            )
        except Exception:
            pass