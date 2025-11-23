from django.contrib import admin
from .models import UserProfile, ChatMessage


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'random_id', 'created_at')
	search_fields = ('user__username', 'random_id')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
	list_display = ('room', 'sender', 'text', 'created_at')
	search_fields = ('room', 'sender__username', 'text')
