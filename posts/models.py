from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True, null=True,
                              related_name="post_group",
                              verbose_name='Группа')
    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True, db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="posts",
                               verbose_name='Автор')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ["-pub_date"]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name="comments",
                             verbose_name='Пост')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="comments",
                               verbose_name='Автор комментария')
    text = models.TextField(max_length=500)
    created = models.DateTimeField(
        'date',
        auto_now_add=True,
        )

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower",
                             null=True
                             )
    author = models.ForeignKey(User,
                               on_delete=models.PROTECT,
                               related_name="following",
                               null=True
                               )

    class Meta:
        unique_together = ["user", "author"]
