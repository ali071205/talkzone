from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from .forms import *
from .models import Profile, FriendRequest


def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username).profile
    else:
        try:
            profile = request.user.profile
        except:
            return redirect_to_login(request.get_full_path())

    is_friend = False
    friend_request = None
    request_sent = False

    if request.user.is_authenticated and username and profile.user != request.user:
        is_friend = profile.friends.filter(id=request.user.id).exists()
        # Check if request already sent
        friend_request = FriendRequest.objects.filter(
            sender=request.user, receiver=profile.user, status='pending'
        ).first()
        request_sent = friend_request is not None

    return render(request, 'a_users/profile.html', {
        'profile': profile,
        'is_friend': is_friend,
        'request_sent': request_sent,
    })


@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)
    if receiver == request.user:
        return redirect('profile', username=username)

    # Check already friends
    if request.user.profile.friends.filter(id=receiver.id).exists():
        messages.info(request, 'Already friends!')
        return redirect('profile', username=username)

    # Create request
    freq, created = FriendRequest.objects.get_or_create(
        sender=request.user, receiver=receiver
    )
    if created:
        messages.success(request, f'Friend request sent to {receiver.profile.name}!')
    else:
        messages.info(request, 'Request already sent.')
    return redirect('profile', username=username)


@login_required
def handle_friend_request(request, request_id, action):
    freq = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)

    if action == 'accept':
        # Add to friends both ways
        request.user.profile.friends.add(freq.sender)
        freq.sender.profile.friends.add(request.user)
        freq.status = 'accepted'
        freq.save()
        messages.success(request, f'You are now friends with {freq.sender.profile.name}! 🎉')
    elif action == 'reject':
        freq.status = 'rejected'
        freq.save()
        messages.info(request, f'Friend request from {freq.sender.profile.name} rejected.')

    return redirect('friend-requests')


@login_required
def friend_requests_view(request):
    pending = FriendRequest.objects.filter(receiver=request.user, status='pending')
    return render(request, 'a_users/friend_requests.html', {'pending': pending})


@login_required
def friends_list_view(request):
    friends = request.user.profile.friends.all()
    return render(request, 'a_users/friends_list.html', {'friends': friends})


@login_required
def remove_friend(request, username):
    other_user = get_object_or_404(User, username=username)
    request.user.profile.friends.remove(other_user)
    other_user.profile.friends.remove(request.user)
    # Also delete friend request records
    FriendRequest.objects.filter(
        sender=request.user, receiver=other_user
    ).delete()
    FriendRequest.objects.filter(
        sender=other_user, receiver=request.user
    ).delete()
    messages.success(request, f'Removed {other_user.profile.name} from friends.')
    return redirect('profile', username=username)


@login_required
def profile_edit_view(request):
    form = ProfileForm(instance=request.user.profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    onboarding = request.path == reverse('profile-onboarding')
    return render(request, 'a_users/profile_edit.html', {'form': form, 'onboarding': onboarding})


@login_required
def profile_settings_view(request):
    return render(request, 'a_users/profile_settings.html')


@login_required
def profile_emailchange(request):
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'partials/email_form.html', {'form': form})
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            form.save()
            send_email_confirmation(request, request.user)
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Email not valid or already in use')
            return redirect('profile-settings')
    return redirect('profile-settings')


@login_required
def profile_usernamechange(request):
    if request.htmx:
        form = UsernameForm(instance=request.user)
        return render(request, 'partials/username_form.html', {'form': form})
    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated!')
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Username not valid or already in use')
            return redirect('profile-settings')
    return redirect('profile-settings')


@login_required
def profile_emailverify(request):
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted.')
        return redirect('home')
    return render(request, 'a_users/profile_delete.html')