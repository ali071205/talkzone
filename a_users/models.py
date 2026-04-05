from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=50, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    friends = models.ManyToManyField(User, related_name='friend_of', blank=True)

    def __str__(self):
        return str(self.user)

    @property
    def name(self):
        if self.displayname:
            return self.displayname
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username

    @property
    def avatar(self):
        if self.image:
            return self.image.url
        return f'{settings.STATIC_URL}images/avatar.svg'

    @property
    def pending_requests_count(self):
        return self.user.received_requests.filter(status='pending').count()



class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.status})"