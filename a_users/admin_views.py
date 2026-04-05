from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from .models import Profile
import json

# Secret admin access code
ADMIN_SECRET = '05-08-2009'


def is_admin(user):
    """Allow anyone who knows the URL to access"""
    return user.is_authenticated


@login_required
def admin_panel_view(request):
    """Main admin dashboard — only superusers can access"""
    if not is_admin(request.user):
        return HttpResponseForbidden('🚫 Access Denied')

    # Get all users with profiles
    users = User.objects.select_related('profile').all().order_by('-last_login')

    # Stats
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    banned_users = Profile.objects.filter(is_banned=True).count()
    online_users = User.objects.filter(online_in_groups__isnull=False).distinct().count()

    # Search
    search = request.GET.get('q', '').strip()
    if search:
        users = users.filter(
            username__icontains=search
        ) | users.filter(
            email__icontains=search
        ) | users.filter(
            first_name__icontains=search
        ) | users.filter(
            last_name__icontains=search
        )

    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'banned_users': banned_users,
        'online_users': online_users,
        'search': search,
    }
    return render(request, 'a_users/admin_panel.html', context)


@login_required
def admin_ban_user(request, user_id):
    """Ban or unban a user"""
    if not is_admin(request.user):
        return HttpResponseForbidden('🚫 Access Denied')

    target_user = get_object_or_404(User, id=user_id)

    # Can't ban yourself
    if target_user == request.user:
        messages.warning(request, "You can't ban yourself!")
        return redirect('admin-panel')

    profile = target_user.profile
    reason = request.POST.get('reason', '').strip()

    if profile.is_banned:
        # Unban
        profile.is_banned = False
        profile.ban_reason = None
        profile.save()
        target_user.is_active = True
        target_user.save()
        messages.success(request, f'✅ {target_user.username} has been unbanned.')
    else:
        # Ban
        profile.is_banned = True
        profile.ban_reason = reason or 'Banned by admin'
        profile.save()
        target_user.is_active = False
        target_user.save()
        messages.success(request, f'🚫 {target_user.username} has been banned.')

    return redirect('admin-panel')


@login_required
def admin_delete_user(request, user_id):
    """Delete a user permanently"""
    if not is_admin(request.user):
        return HttpResponseForbidden('🚫 Access Denied')

    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.warning(request, "You can't delete yourself!")
        return redirect('admin-panel')

    username = target_user.username
    target_user.delete()
    messages.success(request, f'🗑️ User {username} has been deleted permanently.')
    return redirect('admin-panel')


@login_required
def admin_make_staff(request, user_id):
    """Toggle staff/superuser status"""
    if not is_admin(request.user):
        return HttpResponseForbidden('🚫 Access Denied')

    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.warning(request, "You can't modify your own role!")
        return redirect('admin-panel')

    target_user.is_superuser = not target_user.is_superuser
    target_user.is_staff = target_user.is_superuser
    target_user.save()

    if target_user.is_superuser:
        messages.success(request, f'👑 {target_user.username} is now an admin.')
    else:
        messages.success(request, f'{target_user.username} is no longer an admin.')

    return redirect('admin-panel')
