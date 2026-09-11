from django.urls import path

from . import views


urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================

    path(
        "",
        views.home,
        name="home"
    ),


    # =====================================================
    # OPEN CHAT
    # =====================================================

    path(
        "conversation/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail"
    ),


    # =====================================================
    # NEW CHAT
    # =====================================================

    path(
        "new-chat/",
        views.new_chat,
        name="new_chat"
    ),


    # =====================================================
    # SEND MESSAGE
    # =====================================================

    path(
        "send-message/",
        views.send_message,
        name="send_message"
    ),


    # =====================================================
    # DELETE ONE CHAT
    # =====================================================

    path(
        "delete-chat/<int:conversation_id>/",
        views.delete_chat,
        name="delete_chat"
    ),


    # =====================================================
    # DELETE ALL
    # =====================================================

    path(
        "clear-chat/",
        views.clear_chat,
        name="clear_chat"
    ),

]