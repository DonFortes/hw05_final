from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        help_texts = {'text': 'Поле для вашего поста'}
        labels = {
            'text': 'Пишите здесь:',
            'group': 'Выберите группу',
            'image': 'Загрузите изображение'
            }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        help_texts = {'text': 'Поле для вашего комментария'}
        labels = {'text': 'Пишите здесь:'}
