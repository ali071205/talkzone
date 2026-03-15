from django.db import models
from django.contrib.auth.models import User
import shortuuid


class ChatGroup(models.Model):
    group_name = models.CharField(max_length=255, unique=True, default=shortuuid.uuid)
    groupchat_name = models.CharField(max_length=255, null=True, blank=True)
    admin = models.ForeignKey(User, related_name='groupchats', blank=True, null=True, on_delete=models.SET_NULL)
    users_online = models.ManyToManyField(User, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)
    invite_token = models.CharField(max_length=50, unique=True, blank=True)
    max_members = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.invite_token:
            self.invite_token = shortuuid.uuid()
        super().save(*args, **kwargs)

    @property
    def is_full(self):
        if self.max_members:
            return self.members.count() >= self.max_members
        return False

    def __str__(self):
        return self.group_name


class GroupMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
    ]
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username}: {self.body or self.message_type}"

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None

    class Meta:
        ordering = ['-created']


class MessageReaction(models.Model):
    message = models.ForeignKey(GroupMessage, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to msg {self.message.id}"


class GroupJoinRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    group = models.ForeignKey(ChatGroup, related_name='join_requests', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='join_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-created']