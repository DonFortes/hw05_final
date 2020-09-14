from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, Follow, Group, Post, User


class SimpleTest(TestCase):
    def setUp(self):
        self.unlogged = Client()
        self.logged = Client()
        self.user = User.objects.create_user(
            username="sarah",
            email="connor.s@skynet.com",
            password="12345")
        self.user_author = User.objects.create_user(
            username="martin",
            email="martin@skynet.com",
            password="54321")
        self.logged.force_login(self.user)
        self.group = Group.objects.create(title='New_test_group',
                                          slug='new_test_group')
        cache.clear()

    def generate_urls(self, lastpost):
        index = reverse('index')
        profile = reverse('profile', args=[self.user.username])
        post = reverse('post', args=[self.user.username, lastpost.pk])
        group = reverse('group', args=[self.group.slug])
        return [index, profile, post, group]

    def test_profile(self):
        response = self.logged.get(reverse('profile',
                                           args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['author'].username,
                         self.user.username)

    def test_post_create_logged(self):
        response = self.logged.post(reverse("new_post"), {
                'text': "This is my test post",
                'author': self.user,
                'group': self.group.id
            },
            follow=True
        )
        cache.clear()
        self.assertTrue(
            Post.objects.all().exists()
            )
        lastpost = Post.objects.latest('pub_date')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(lastpost.text, 'This is my test post')
        self.assertEqual(lastpost.author.username, 'sarah')
        self.assertEqual(lastpost.group.title, 'New_test_group')

    def test_post_create_unlogged(self):
        content = {'group': self.group.id, 'text': 'test_text'}
        response = self.unlogged.post(reverse('new_post'),
                                      content, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Post.objects.all().exists()
            )

    def test_new_post_everywhere(self):
        post = Post.objects.create(text='New_test_post',
                                        author=self.user,
                                        group=self.group)

        urls = self.generate_urls(post)
        for url in urls:
            response = self.logged.get(url)
            self.assertContains(response, 'New_test_post')
            self.assertEqual(response.status_code, 200)

    def test_edit(self):
        post = Post.objects.create(text='New_test_post',
                                        author=self.user,
                                        group=self.group)
        content = {'group': self.group.id, 'author': self.user, 'text': 'edit'}
        self.logged.post(reverse('post_edit', args=[self.user.username,
                                 post.id]), content, follow=True)

        urls = self.generate_urls(post)
        for url in urls:
            response = self.logged.get(url)
            self.assertContains(response, 'edit')
            self.assertEqual(response.status_code, 200)

    def test_404(self):
        response = self.unlogged.get('something/really/weird/')
        self.assertEqual(response.status_code, 404)

    def test_image(self):

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            'small.gif',
            small_gif,
            content_type='image/gif'
            )

        content = {
            'author': self.logged,
            'text': 'post with image',
            'group': self.group.id,
            'image': img,
            }

        response = self.logged.post(reverse('new_post'), content, follow=True)
        self.assertContains(response, '<img'.encode())

        lastpost = Post.objects.latest('pub_date')

        urls = self.generate_urls(lastpost)
        for url in urls:
            response = self.logged.get(url)
            self.assertContains(response, '<img'.encode())
            self.assertEqual(response.status_code, 200)

    def test_wrong_file(self):
        wrong_file = (
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        wrong = SimpleUploadedFile(
            "wrong_file.doc",
            wrong_file,
            content_type="doc"
        )
        url = reverse("new_post")
        data = {
            "text": "Wrong image",
            "group": self.group.id,
            "image": wrong
        }
        response = self.logged.post(url, data=data)
        self.assertFormError(
            response,
            form="form",
            field="image",
            errors="Загрузите правильное изображение. Файл, "
                   "который вы загрузили, поврежден или не "
                   "является изображением.")

    def test_cache(self):
        Post.objects.create(text='New_test_post',
                                        author=self.user,
                                        group=self.group)
        response = self.logged.get(reverse("index"))
        cache_test = response["Cache-Control"]
        self.assertEqual(cache_test, "max-age=20")
        self.assertEqual(len(response.context["page"]), 1)
        self.post_test = Post.objects.create(
            text="Post test",
            author=self.user,
            group=self.group
        )
        response = self.logged.get(reverse("index"))
        self.assertIsNone(response.context)
        cache.clear()
        response = self.logged.get(reverse("index"))
        self.assertEqual(len(response.context["page"]), 2)

    def test_logged_follow(self):
        self.logged.get(
            reverse('profile_follow', args=['martin']),
            follow=True)

        follows = Follow.objects.all()
        self.assertEqual(len(follows), 1)

        follow = follows[0]
        self.assertEqual(follow.user.username, 'sarah')
        self.assertEqual(follow.author.username, 'martin')

    def test_unlogged_follow(self):
        self.unlogged.get(
            reverse('profile_follow', args=['martin']),
            follow=True)

        follows = Follow.objects.all()
        self.assertEqual(len(follows), 0)

    def test_logged_unfollow(self):
        Follow.objects.create(
            author=self.user_author, user=self.user)
        self.logged.get(
            reverse('profile_unfollow', args=['martin']), follow=True)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user_author).exists())

    def test_post_on_follow_page(self):
        post = Post.objects.create(
            text='New_test_post', author=self.user_author,
            group=self.group)
        Follow.objects.create(
            author=self.user_author, user=self.user)
        post_view = self.logged.get(reverse('follow_index'))
        page = post_view.context['page']
        post2 = page[0]
        self.assertEqual(post.text, post2.text)
        self.assertEqual(post.group, post2.group)

    def test_post_on_unfollow_page(self):
        post = Post.objects.create(
            text='New_test_post', author=self.user_author,
            group=self.group)
        response = self.logged.get(reverse('follow_index'))
        page = response.context["page"]
        count = len(page)
        self.assertEqual(count, 0)

    def test_comment_logged(self):

        post = Post.objects.create(
            text='New_test_post', author=self.user_author,
            group=self.group)

        response = self.logged.post(
            reverse('add_comment', args=[self.user_author, post.id]),
            {
                'text': 'Comment',
                'author': self.user
            },
            follow=True)

        comments = response.context["items"]
        comment = comments[0]
        db_comment = Comment.objects.latest("created")

        self.assertEqual(comment.author, db_comment.author)
        self.assertEqual(comment.text, db_comment.text)

    def test_comment_unlogged(self):

        post = Post.objects.create(
            text='New_test_post', author=self.user_author,
            group=self.group)

        response = self.unlogged.post(
            reverse('add_comment', args=[self.user_author, post.id]),
            {
                'text': 'Comment'
            },
            follow=True)

        comments = Comment.objects.all()
        self.assertEqual(len(comments), 0)
