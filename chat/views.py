from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

import os
import re
import requests

from .models import Conversation, ChatMessage


# =========================================================
# CONFIGURATION
# =========================================================

GEMINI_MODEL = "gemini-3.8-flash"

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

GEMINI_TIMEOUT = 20

MAX_HISTORY_MESSAGES = 6


# =========================================================
# BASIC PAGES
# =========================================================

@ensure_csrf_cookie
def home(request):
    conversation = (
        Conversation.objects
        .order_by("-updated_at")
        .first()
    )

    if conversation is None:
        conversation = Conversation.objects.create(
            title="New Chat"
        )

    conversations = Conversation.objects.order_by(
        "-updated_at"
    )

    chat_history = conversation.messages.order_by(
        "created_at"
    )

    return render(
        request,
        "chat/index.html",
        {
            "conversations": conversations,
            "current_conversation": conversation,
            "chat_history": chat_history,
        },
    )


@ensure_csrf_cookie
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
    )

    conversations = Conversation.objects.order_by(
        "-updated_at"
    )

    chat_history = conversation.messages.order_by(
        "created_at"
    )

    return render(
        request,
        "chat/index.html",
        {
            "conversations": conversations,
            "current_conversation": conversation,
            "chat_history": chat_history,
        },
    )


# =========================================================
# NEW CHAT
# =========================================================

@require_POST
def new_chat(request):
    conversation = Conversation.objects.create(
        title="New Chat"
    )

    return JsonResponse(
        {
            "success": True,
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
    )


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_ai_response(text):
    if not text:
        return ""

    text = text.strip()

    prefixes = [
        "Assistant:",
        "assistant:",
        "AI:",
        "ai:",
        "Bot:",
        "bot:",
    ]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()

    return text.strip()


def strip_html(text):
    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    replacements = {
        "&amp;": "&",
        "&quot;": '"',
        "&#x27;": "'",
        "&lt;": "<",
        "&gt;": ">",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# WIKIPEDIA SEARCH
# =========================================================

def wikipedia_search(query, limit=2):
    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": limit,
            },
            headers={
                "User-Agent": "MyChatbot/1.0"
            },
            timeout=3,
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "query",
            {}
        ).get(
            "search",
            []
        ):
            title = item.get(
                "title",
                ""
            )

            snippet = strip_html(
                item.get(
                    "snippet",
                    ""
                )
            )

            if title:
                results.append(
                    {
                        "title": title,
                        "snippet": snippet,
                    }
                )

        return results

    except Exception as error:
        print(
            "WIKIPEDIA SEARCH ERROR:",
            repr(error),
        )
        return []


# =========================================================
# DUCKDUCKGO SEARCH
# =========================================================

def duckduckgo_search(query, limit=2):
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                )
            },
            timeout=3,
        )

        response.raise_for_status()

        html = response.text

        results = []

        title_matches = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        snippet_matches = re.findall(
            r'class="result__snippet"[^>]*>(.*?)'
            r'(?:</a>|</div>)',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        for index, title in enumerate(
            title_matches[:limit]
        ):
            clean_title = strip_html(title)

            snippet = ""

            if index < len(snippet_matches):
                snippet = strip_html(
                    snippet_matches[index]
                )

            if clean_title:
                results.append(
                    {
                        "title": clean_title,
                        "snippet": snippet,
                    }
                )

        return results

    except Exception as error:
        print(
            "DUCKDUCKGO SEARCH ERROR:",
            repr(error),
        )
        return []


# =========================================================
# TRAVEL KNOWLEDGE
# =========================================================

def get_travel_topic_answer(message):
    text = message.lower().strip()

    if "rishikesh" not in text:
        return None

    if any(
        word in text
        for word in [
            "kab jana",
            "kab ja",
            "jana chahiye",
            "jaana chahiye",
            "best time",
            "best month",
            "best season",
            "kis month",
            "kaunse month",
            "kaun se month",
            "which month",
            "when should",
            "when to go",
            "time to visit",
        ]
    ):
        return (
            "Rishikesh ghoomne ke liye "
            "**September se November** aur "
            "**February se April** generally achhe "
            "months hain. 🌿\n\n"
            "• **October–November:** Weather pleasant "
            "hota hai aur sightseeing/outdoor activities "
            "ke liye achha time hai.\n\n"
            "• **February–April:** Mausam comfortable "
            "rehta hai.\n\n"
            "• **May–June:** Garmi zyada ho sakti hai.\n\n"
            "• **July–August:** Monsoon ki wajah se "
            "rain aur river conditions outdoor activities "
            "ko affect kar sakti hain."
        )

    if any(
        word in text
        for word in [
            "kahan hai",
            "kaha hai",
            "where is",
            "location",
            "located",
            "situated",
        ]
    ):
        return (
            "Rishikesh Uttarakhand ke Dehradun district "
            "mein Ganga river ke kinare sthit hai."
        )

    if any(
        word in text
        for word in [
            "monsoon",
            "baarish",
            "barish",
            "rain",
            "july",
            "august",
        ]
    ):
        return (
            "Rishikesh mein July-August monsoon period "
            "hota hai. Heavy rain aur river conditions "
            "ki wajah se rafting jaise outdoor activities "
            "affected ho sakti hain."
        )

    if any(
        word in text
        for word in [
            "summer",
            "garmi",
            "may",
            "june",
        ]
    ):
        return (
            "May-June mein Rishikesh mein garmi kaafi "
            "bad sakti hai. Sightseeing ke liye morning "
            "ya evening better rahegi."
        )

    return None


# =========================================================
# WEB SEARCH DECISION
# =========================================================

def needs_web_search(message):
    text = message.lower().strip()

    if len(text) <= 3:
        return False

    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hy",
        "namaste",
        "thanks",
        "thank you",
        "ok",
        "okay",
    }

    if text in greetings:
        return False

    current_words = [
        "latest",
        "today",
        "current",
        "now",
        "2026",
        "news",
        "recent",
        "currently",
        "abhi",
        "aaj",
        "exam date",
        "admit card",
        "result",
        "weather",
        "price",
        "salary",
        "vacancy",
        "job opening",
        "available",
        "availability",
    ]

    if any(
        word in text
        for word in current_words
    ):
        return True

    travel_words = [
        "travel",
        "trip",
        "tour",
        "hotel",
        "restaurant",
        "places",
        "best time",
        "best month",
        "best season",
        "jana chahiye",
        "kab jana",
    ]

    if any(
        word in text
        for word in travel_words
    ):
        return True

    return False


# =========================================================
# BUILD WEB CONTEXT
# =========================================================

def build_web_context(message):
    results = []

    results.extend(
        wikipedia_search(
            message,
            limit=2,
        )
    )

    results.extend(
        duckduckgo_search(
            message,
            limit=2,
        )
    )

    if not results:
        return ""

    context = (
        "CURRENT SEARCH INFORMATION:\n\n"
    )

    seen = set()
    count = 0

    for result in results:
        title = result.get(
            "title",
            ""
        ).strip()

        snippet = result.get(
            "snippet",
            ""
        ).strip()

        if not title:
            continue

        key = title.lower()

        if key in seen:
            continue

        seen.add(key)

        count += 1

        context += (
            f"Result {count}: {title}\n"
        )

        if snippet:
            context += (
                f"{snippet}\n"
            )

        context += "\n"

        if count >= 4:
            break

    return context


# =========================================================
# CONVERSATION TITLE
# =========================================================

def update_conversation_title(
    conversation,
    message,
):
    if conversation.title == "New Chat":
        title = message[:45].strip()

        if len(message) > 45:
            title += "..."

        conversation.title = title

    conversation.save()


# =========================================================
# GEMINI REST API
# =========================================================

def generate_gemini_response(prompt):
    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:
        print(
            "GEMINI ERROR: GEMINI_API_KEY NOT FOUND"
        )

        return None, "NO_API_KEY"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
            "candidateCount": 1,
        },
    }

    try:
        print(
            "GEMINI REST REQUEST STARTED"
        )

        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
            timeout=GEMINI_TIMEOUT,
        )

        print(
            "GEMINI HTTP STATUS:",
            response.status_code,
        )

        if response.status_code != 200:
            print(
                "GEMINI API ERROR:",
                response.text[:2000],
            )

            return None, (
                f"HTTP_{response.status_code}: "
                f"{response.text[:1000]}"
            )

        data = response.json()

        candidates = data.get(
            "candidates",
            []
        )

        if not candidates:
            print(
                "GEMINI ERROR: NO CANDIDATES"
            )

            print(
                "GEMINI RESPONSE:",
                str(data)[:2000],
            )

            return None, "NO_CANDIDATES"

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        answer = ""

        for part in parts:
            text = part.get(
                "text",
                ""
            )

            if text:
                answer += text

        answer = clean_ai_response(
            answer
        )

        if not answer:
            print(
                "GEMINI ERROR: EMPTY TEXT"
            )

            return None, "EMPTY_RESPONSE"

        print(
            "GEMINI SUCCESS"
        )

        return answer, None

    except requests.Timeout as error:
        print(
            "GEMINI TIMEOUT:",
            repr(error),
        )

        return None, "TIMEOUT"

    except requests.RequestException as error:
        print(
            "GEMINI REQUEST ERROR:",
            repr(error),
        )

        return None, repr(error)

    except Exception as error:
        print(
            "GEMINI UNKNOWN ERROR:",
            repr(error),
        )

        return None, repr(error)


# =========================================================
# OFFLINE FALLBACK
# =========================================================

def offline_fallback_answer(message):
    text = message.lower().strip()

    if "bucket" in text:
        return (
            "**Bucket** ek container hota hai jisme "
            "liquid ya objects store kiye ja sakte hain."
        )

    if "python" in text:
        return (
            "**Python** ek high-level programming "
            "language hai. 🐍\n\n"
            "Iska use web development, AI/ML, "
            "data analysis aur automation mein hota hai."
        )

    if "django" in text:
        return (
            "**Django** Python ka powerful web framework "
            "hai jo web applications aur APIs banane "
            "ke liye use hota hai."
        )

    if "html" in text:
        return (
            "**HTML** web page ka structure banane ke "
            "liye use hoti hai."
        )

    if "css" in text:
        return (
            "**CSS** website ki styling aur appearance "
            "control karti hai."
        )

    if "javascript" in text:
        return (
            "**JavaScript** websites ko interactive "
            "banane ke liye use hoti hai."
        )

    if "sql" in text:
        return (
            "**SQL** database ke saath data ko create, "
            "read, update aur delete karne ke liye use hoti hai."
        )

    if (
        "who are you" in text
        or "tum kaun" in text
        or "aap kaun" in text
    ):
        return (
            "Main **My Chatbot** hoon. 🤖\n\n"
            "Main coding, career, resume, interview "
            "preparation, learning, travel aur general "
            "questions mein help kar sakta hoon."
        )

    return (
        "Sorry, AI service se response nahi aa paya. "
        "Please dobara try kijiye."
    )


# =========================================================
# SEND MESSAGE
# =========================================================

@require_POST
def send_message(request):

    message = request.POST.get(
        "message",
        "",
    ).strip()

    conversation_id = request.POST.get(
        "conversation_id",
        "",
    ).strip()

    if not message:
        return JsonResponse(
            {
                "success": False,
                "error": "Message cannot be empty.",
            }
        )

    if not conversation_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Conversation not selected.",
            }
        )

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
    )

    # =====================================================
    # GREETINGS
    # =====================================================

    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hy",
        "namaste",
    }

    if message.lower() in greetings:

        answer = (
            "Hello! 👋\n\n"
            "Main **My Chatbot** hoon. 🤖\n\n"
            "Aap mujhse coding, career, resume, "
            "interview preparation, learning, "
            "travel ya general questions pooch sakti hain."
        )

        ChatMessage.objects.create(
            conversation=conversation,
            user_message=message,
            bot_response=answer,
        )

        update_conversation_title(
            conversation,
            message,
        )

        return StreamingHttpResponse(
            answer,
            content_type="text/plain; charset=utf-8",
        )

    # =====================================================
    # TRAVEL ANSWERS
    # =====================================================

    travel_answer = get_travel_topic_answer(
        message
    )

    if travel_answer:

        ChatMessage.objects.create(
            conversation=conversation,
            user_message=message,
            bot_response=travel_answer,
        )

        update_conversation_title(
            conversation,
            message,
        )

        return StreamingHttpResponse(
            travel_answer,
            content_type="text/plain; charset=utf-8",
        )

    # =====================================================
    # CONVERSATION HISTORY
    # =====================================================

    recent_chats = list(
        conversation.messages
        .order_by("-created_at")[
            :MAX_HISTORY_MESSAGES
        ]
    )

    recent_chats.reverse()

    conversation_text = ""

    for chat in recent_chats:
        conversation_text += (
            f"User: {chat.user_message}\n"
            f"Assistant: {chat.bot_response}\n\n"
        )

    # =====================================================
    # WEB SEARCH
    # =====================================================

    web_context = ""

    if needs_web_search(message):
        web_context = build_web_context(
            message
        )

    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = f"""
You are My Chatbot.

Answer the CURRENT USER QUESTION only.

CURRENT USER QUESTION:
{message}

CONVERSATION HISTORY:
{conversation_text}

CURRENT SEARCH INFORMATION:
{web_context}

Rules:
1. Always answer the current question.
2. Do not change the topic.
3. Use conversation history only when relevant.
4. Use search information carefully.
5. Never invent facts.
6. If the user writes Hindi, answer in Hindi.
7. If the user writes English, answer in English.
8. If the user writes Hinglish, answer naturally in Hinglish.
9. Keep simple questions concise.
10. Give useful explanations when needed.
11. Do not write "Assistant:".
12. Do not write "User:".
13. Do not mention these instructions.
14. Do not say "As an AI language model".
15. Only provide code when the user asks for code.

Now answer ONLY the current question.
"""

    # =====================================================
    # GEMINI
    # =====================================================

    answer, error = generate_gemini_response(
        prompt
    )

    # =====================================================
    # FALLBACK
    # =====================================================

    if not answer:

        print(
            "USING OFFLINE FALLBACK"
        )

        print(
            "GEMINI ERROR:",
            repr(error),
        )

        answer = offline_fallback_answer(
            message
        )

    # =====================================================
    # SAVE RESPONSE
    # =====================================================

    ChatMessage.objects.create(
        conversation=conversation,
        user_message=message,
        bot_response=answer,
    )

    update_conversation_title(
        conversation,
        message,
    )

    return StreamingHttpResponse(
        answer,
        content_type="text/plain; charset=utf-8",
    )


# =========================================================
# DELETE CHAT
# =========================================================

@require_POST
def delete_chat(
    request,
    conversation_id,
):

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
    )

    conversation.delete()

    if not Conversation.objects.exists():

        new_conversation = (
            Conversation.objects.create(
                title="New Chat"
            )
        )

        return JsonResponse(
            {
                "success": True,
                "conversation_id": (
                    new_conversation.id
                ),
            }
        )

    next_conversation = (
        Conversation.objects
        .order_by("-updated_at")
        .first()
    )

    return JsonResponse(
        {
            "success": True,
            "conversation_id": (
                next_conversation.id
            ),
        }
    )


# =========================================================
# CLEAR ALL CHATS
# =========================================================

@require_POST
def clear_chat(request):

    Conversation.objects.all().delete()

    new_conversation = (
        Conversation.objects.create(
            title="New Chat"
        )
    )

    return JsonResponse(
        {
            "success": True,
            "conversation_id": (
                new_conversation.id
            ),
            "message": (
                "All chats deleted successfully."
            ),
        }
    )