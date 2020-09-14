from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix="index_page")
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.post_group.all()
    paginator = Paginator(group_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group,
         'page': page,
         'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect('index')
    labels = {
        "title": "Добавить запись",
        "button": "Добавить"
    }
    return render(request, 'post_new.html', {
        'form': form,
        'labels': labels})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated:
        user = request.user
        if Follow.objects.filter(user=user, author=author).exists():
            following = True
        else:
            following = False
        context = {
            'author': author,
            'page': page,
            'paginator': paginator,
            'following': following,
            "username": author,
        }
        return render(request, 'profile.html', context)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator, 'author': author}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request, "post_view.html",
        {
            "post": post,
            "author": author,
            "form": form,
            "items": comments
        }
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse(
        "post",
        kwargs={"username": username, "post_id": post_id}
    )
    if post.author != request.user:
        return redirect(url)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect(url)

    labels = {
        "title": "Редактировать запись",
        "button": "Сохранить"
    }

    return render(
        request,
        'post_new.html',
        {
            "form": form,
            "labels": labels,
            "post": post
        }
    )


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    url = reverse(
        "post",
        kwargs={"username": username, "post_id": post_id}
    )
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.instance.author = request.user
            form.instance.post = post
            form.save()
            return redirect(url)
    return redirect(url)


@login_required
def follow_index(request):
    logged = request.user
    posts = Post.objects.filter(author__following__user=logged)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'follow.html',
        {'page': page, 'paginator': paginator}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    url = reverse("profile", args=[username])
    user = request.user
    if author != user:
        Follow.objects.get_or_create(
            user=user,
            author=author
        )
    return redirect(url)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    url = reverse("profile", args=[username])
    user = request.user
    if Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.filter(user=user, author=author).delete()
        return redirect(url)

