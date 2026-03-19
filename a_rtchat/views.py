from asgiref.sync import async_to_sync
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ChatGroup, GroupMessage, GroupJoinRequest, MessageReaction
from .forms import ChatMessageCreateForm, NewGroupForm as GroupChatCreateForm, ChatRoomEditForm
from django.http import Http404, JsonResponse
import shortuuid
import json


@login_required
def chat_view(request, chatroom_name="public-chat"):
    # Public chat na mile toh automatically bana do
    chat_group, created = ChatGroup.objects.get_or_create(
        group_name=chatroom_name,
        defaults={
            'groupchat_name': 'Public Chat',
            'is_private': False,
        }
    )

    # User ko automatically member bana do
    if request.user not in chat_group.members.all():
        chat_group.members.add(request.user)

    chat_messages = chat_group.chat_messages.all()[:50]
    form = ChatMessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    join_request = None
    if chat_group.groupchat_name:
        join_request = GroupJoinRequest.objects.filter(
            group=chat_group, user=request.user, status='pending'
        ).first()

    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {'message': message, 'user': request.user}
            return render(request, 'partials/chat_message_p.html', context)

    context = {
        'chat_messages': chat_messages,
        'form': form,
        'other_user': other_user,
        'chatroom_name': chatroom_name,
        'chat_group': chat_group,
        'join_request': join_request,
    }
    return render(request, 'chat.html', context)


@login_required
def toggle_reaction(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        new_emoji = data.get('emoji', '')
    except Exception:
        return JsonResponse({'error': 'bad request'}, status=400)

    message = get_object_or_404(GroupMessage, id=message_id)

    existing = MessageReaction.objects.filter(message=message, user=request.user).first()

    if existing:
        if existing.emoji == new_emoji:
            existing.delete()
        else:
            existing.emoji = new_emoji
            existing.save()
    else:
        MessageReaction.objects.create(message=message, user=request.user, emoji=new_emoji)

    reaction_data = {}
    for r in message.reactions.all().select_related('user__profile'):
        if r.emoji not in reaction_data:
            reaction_data[r.emoji] = {'count': 0, 'users': []}
        reaction_data[r.emoji]['count'] += 1
        name = r.user.profile.name if hasattr(r.user, 'profile') else r.user.username
        reaction_data[r.emoji]['users'].append(name)

    return JsonResponse({'reactions': reaction_data})


@login_required
def get_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    other_user = get_object_or_404(User, username=username)
    my_chatrooms = request.user.chat_groups.filter(is_private=True)
    chatroom = None
    for room in my_chatrooms:
        if other_user in room.members.all():
            chatroom = room
            break
    if not chatroom:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(request.user, other_user)
    return redirect('chat-room', chatroom_name=chatroom.group_name)


@login_required
def create_groupchat(request):
    form = GroupChatCreateForm()
    if request.method == 'POST':
        form = GroupChatCreateForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            group.members.add(request.user)
            return redirect('chat-room', chatroom_name=group.group_name)
    return render(request, 'create_groupchat.html', {'form': form})


@login_required
def groupchat_edit(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    form = ChatRoomEditForm(instance=chat_group)
    if request.method == 'POST':
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()
            return redirect('groupchat-edit', chatroom_name=chatroom_name)
    join_requests = chat_group.join_requests.filter(status='pending')
    return render(request, 'groupchat_edit.html', {
        'form': form, 'chat_group': chat_group, 'join_requests': join_requests
    })


@login_required
def groupchat_delete(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    if request.method == 'POST':
        chat_group.delete()
        return redirect('home')
    return render(request, 'groupchat_delete.html', {'chat_group': chat_group})


@login_required
def groupchat_leave(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user == chat_group.admin:
        chat_group.delete()
        return redirect('home')
    chat_group.members.remove(request.user)
    return redirect('home')


@login_required
def groupchat_invite(request, invite_token):
    chat_group = get_object_or_404(ChatGroup, invite_token=invite_token)
    if request.user in chat_group.members.all():
        return redirect('chat-room', chatroom_name=chat_group.group_name)
    return render(request, 'groupchat_invite.html', {'chat_group': chat_group})


@login_required
def send_join_request(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if chat_group.is_full:
        return render(request, 'join_request_sent.html', {
            'chat_group': chat_group, 'error': 'This guild is full!'
        })
    if request.user not in chat_group.members.all():
        GroupJoinRequest.objects.get_or_create(group=chat_group, user=request.user)
    return redirect('join-request-sent', chatroom_name=chatroom_name)


@login_required
def join_request_sent(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    return render(request, 'join_request_sent.html', {'chat_group': chat_group})


@login_required
def handle_join_request(request, request_id, action):
    join_request = get_object_or_404(GroupJoinRequest, id=request_id)
    if request.user != join_request.group.admin:
        raise Http404()
    if action == 'approve':
        if not join_request.group.is_full:
            join_request.group.members.add(join_request.user)
            join_request.status = 'approved'
        else:
            join_request.status = 'rejected'
        join_request.save()
    elif action == 'reject':
        join_request.status = 'rejected'
        join_request.save()
    return redirect('notifications')


@login_required
def notifications_view(request):
    my_groups = request.user.groupchats.all()
    pending_requests = GroupJoinRequest.objects.filter(
        group__in=my_groups, status='pending'
    )
    return render(request, 'notifications.html', {'pending_requests': pending_requests})


@login_required
def search_groups(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = ChatGroup.objects.filter(
            groupchat_name__icontains=query, is_private=False
        ).exclude(members=request.user)
    return render(request, 'search_groups.html', {'results': results, 'query': query})


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(GroupMessage, id=message_id)
    if request.user == message.author or request.user == message.group.admin:
        message.delete()
    return redirect('chat-room', chatroom_name=message.group.group_name)


@login_required
def upload_file(request, chatroom_name):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if chat_group.groupchat_name and request.user not in chat_group.members.all():
        return JsonResponse({'error': 'Not a member'}, status=403)
    if chat_group.is_private and request.user not in chat_group.members.all():
        return JsonResponse({'error': 'Not allowed'}, status=403)

    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file'}, status=400)

    content_type = file.content_type or ''
    if content_type.startswith('image/'):
        msg_type = 'image'
    elif content_type.startswith('video/'):
        msg_type = 'video'
    elif content_type.startswith('audio/'):
        msg_type = 'audio'
    else:
        msg_type = 'file'

    if file.size > 20 * 1024 * 1024:
        return JsonResponse({'error': 'File too large (max 20MB)'}, status=400)

    message = GroupMessage.objects.create(
        group=chat_group,
        author=request.user,
        file=file,
        message_type=msg_type,
        body=file.name,
    )

    from django.template.loader import render_to_string
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        chatroom_name,
        {
            "type": "message_handler",
            "message_id": message.id,
        }
    )

    return JsonResponse({'success': True, 'message_id': message.id})


# ── AI BOT ──
import requests as http_requests
import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def ask_groq(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": "You are TalkZone AI — a helpful, friendly assistant built into TalkZone chat app. Answer questions clearly and concisely. You can help with coding, general knowledge, math, advice, and anything else. Keep responses under 400 words unless asked for more."
        }
    ]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        res = http_requests.post(
            GROQ_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            },
            timeout= 120
        )
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Sorry, I couldn't process that. Error: {str(e)}"


@login_required
def bot_reply(request, chatroom_name):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    recent = list(chat_group.chat_messages.filter(
        body__isnull=False, message_type='text'
    ).order_by('-created')[:8])
    recent.reverse()

    history = []
    for msg in recent:
        if msg.body and not msg.body.startswith('@bot'):
            role = "assistant" if msg.author.username == 'talkzone_bot' else "user"
            history.append({"role": role, "content": msg.body})

    bot_response = ask_groq(user_message, history)

    bot_user, created = User.objects.get_or_create(username='talkzone_bot')
    if created:
        bot_user.first_name = 'TalkZone'
        bot_user.last_name = 'AI'
        bot_user.save()
        from a_users.models import Profile
        Profile.objects.get_or_create(user=bot_user)

    from channels.layers import get_channel_layer
    bot_msg = GroupMessage.objects.create(
        group=chat_group,
        author=bot_user,
        body=f"🤖 {bot_response}",
        message_type='text'
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        chatroom_name,
        {"type": "message_handler", "message_id": bot_msg.id}
    )

    return JsonResponse({'success': True})