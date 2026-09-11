from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user_message", "bot_response", "created_at")
    search_fields = ("user_message", "bot_response")