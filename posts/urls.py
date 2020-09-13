from django.urls import path

from . import views

urlpatterns = [
    path(
        "<username>/<int:post_id>/comment",
        views.add_comment, name="add_comment"
        ),
    path('new/', views.new_post, name='new_post'),
    path("follow/", views.follow_index, name="follow_index"),
    path("", views.index, name="index"),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path(
            '<str:username>/<int:post_id>/edit/',
            views.post_edit,
            name='post_edit'
        ),
    path("group/<slug:slug>/", views.group_posts, name='group'),
    path("404/", views.page_not_found, name='404'),
    path("505/", views.server_error, name='500'),

    path(
        "<str:username>/follow/",
        views.profile_follow,
        name="profile_follow"
        ),
    path(
        "<str:username>/unfollow/",
        views.profile_unfollow,
        name="profile_unfollow"
        ),
]
