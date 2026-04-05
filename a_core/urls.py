from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from a_users.views import profile_view, CustomLoginView
from a_users.admin_views import admin_panel_view, admin_ban_user, admin_delete_user, admin_make_staff

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', CustomLoginView.as_view(template_name='account/login.html'), name='account_login'),
    path('accounts/', include('allauth.urls')),
    path('', include('a_rtchat.urls')),
    path('profile/', include('a_users.urls')),
    path('@<username>/', profile_view, name="profile"),

    # Secret Admin Panel
    path('05-08-2009/', admin_panel_view, name='admin-panel'),
    path('05-08-2009/ban/<int:user_id>/', admin_ban_user, name='admin-ban-user'),
    path('05-08-2009/delete/<int:user_id>/', admin_delete_user, name='admin-delete-user'),
    path('05-08-2009/staff/<int:user_id>/', admin_make_staff, name='admin-make-staff'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]