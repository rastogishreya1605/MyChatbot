from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

import requests
import json
import re
from urllib.parse import quote

from .models import Conversation, ChatMessage


# =========================================================
# CONFIG
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"

MAX_HISTORY_MESSAGES = 4


# =========================================================
# HOME
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

    conversations = (
        Conversation.objects
        .order_by("-updated_at")
    )

    chat_history = (
        conversation.messages
        .order_by("created_at")
    )

    return render(
        request,
        "chat/index.html",
        {
            "conversations": conversations,
            "current_conversation": conversation,
            "chat_history": chat_history,
        }
    )


# =========================================================
# CONVERSATION DETAIL
# =========================================================

@ensure_csrf_cookie
def conversation_detail(request, conversation_id):

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
    )

    conversations = (
        Conversation.objects
        .order_by("-updated_at")
    )

    chat_history = (
        conversation.messages
        .order_by("created_at")
    )

    return render(
        request,
        "chat/index.html",
        {
            "conversations": conversations,
            "current_conversation": conversation,
            "chat_history": chat_history,
        }
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
# CLEAN AI RESPONSE
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

    text = re.sub(
        r"\n?(User|Assistant|AI|Bot):\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


# =========================================================
# REMOVE HTML
# =========================================================

def strip_html(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = (
        text
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#x27;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# WIKIPEDIA SEARCH
# =========================================================
#
# Reliable factual fallback.
# This avoids depending only on a search-engine HTML layout.
# =========================================================

def wikipedia_search(query, limit=4):

    try:

        api_url = (
            "https://en.wikipedia.org/w/api.php"
        )

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": limit,
        }

        response = requests.get(
            api_url,
            params=params,
            headers={
                "User-Agent":
                    "MyChatbot/1.0"
            },
            timeout=8
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
            error
        )

        return []


# =========================================================
# DUCKDUCKGO SEARCH
# =========================================================

def duckduckgo_search(query, limit=5):

    try:

        url = (
            "https://html.duckduckgo.com/html/?q="
            + quote(query)
        )

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/131.0 Safari/537.36"
            },
            timeout=8
        )

        response.raise_for_status()

        html = response.text

        results = []

        # Extract result titles
        title_matches = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Extract snippets
        snippet_matches = re.findall(
            r'class="result__snippet"[^>]*>(.*?)'
            r'(?:</a>|</div>)',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )

        for index, title in enumerate(
            title_matches[:limit]
        ):

            clean_title = strip_html(
                title
            )

            snippet = ""

            if index < len(
                snippet_matches
            ):

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
            error
        )

        return []


# =========================================================
# SPECIAL TRAVEL KNOWLEDGE
# =========================================================
#
# Important stable information is kept here so a local LLM
# cannot replace "best time" with an unrelated location answer.
# =========================================================

TRAVEL_KNOWLEDGE = {

    "rishikesh": {
        "best_time": (
            "Rishikesh ghoomne ke liye generally "
            "September se November aur February se April "
            "achha time maana jata hai. "
            "October-November mein weather pleasant hota hai "
            "aur outdoor activities ke liye achha season hota hai."
        ),

        "monsoon": (
            "July-August mein monsoon hota hai. "
            "Is period mein heavy rain aur river conditions "
            "ki wajah se outdoor activities, especially rafting, "
            "weather aur local authorities/operators ke according "
            "affected ho sakti hain."
        ),

        "summer": (
            "May-June mein temperature kaafi badh sakta hai, "
            "isliye sightseeing ke liye subah ya shaam better "
            "reh sakta hai."
        ),

        "winter": (
            "December-January mein weather cooler hota hai. "
            "Sightseeing aur yoga ke liye time theek ho sakta hai, "
            "lekin subah-shaam thand hoti hai."
        ),

        "location": (
            "Rishikesh Uttarakhand ke Dehradun district mein "
            "Ganga river ke kinare sthit hai."
        ),
    }
}


# =========================================================
# DETECT TRAVEL TOPIC
# =========================================================

def get_travel_topic_answer(message):

    text = message.lower().strip()

    # Rishikesh topic
    if "rishikesh" not in text:
        return None

    # -----------------------------------------------------
    # BEST TIME / KAB JANA
    # -----------------------------------------------------

    best_time_words = [
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

    if any(
        word in text
        for word in best_time_words
    ):

        return (
            "Rishikesh ghoomne ke liye **September se November** "
            "aur **February se April** generally best months hain. 🌿\n\n"
            "• **October–November:** Weather pleasant hota hai, "
            "sightseeing aur outdoor activities ke liye bahut achha.\n"
            "• **February–April:** Mausam comfortable rehta hai "
            "aur outdoor activities ke liye suitable hota hai.\n"
            "• **May–June:** Garmi zyada ho sakti hai.\n"
            "• **July–August:** Monsoon ki wajah se rain aur river "
            "conditions outdoor activities ko affect kar sakti hain.\n\n"
            "**Agar tum specifically rafting + sightseeing ke liye "
            "ja rahi ho, to October–November ek strong choice hai.**"
        )

    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    location_words = [
        "kahan hai",
        "kaha hai",
        "where is",
        "location",
        "located",
        "situated",
    ]

    if any(
        word in text
        for word in location_words
    ):

        return TRAVEL_KNOWLEDGE[
            "rishikesh"
        ][
            "location"
        ]

    # -----------------------------------------------------
    # MONSOON
    # -----------------------------------------------------

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

        return TRAVEL_KNOWLEDGE[
            "rishikesh"
        ][
            "monsoon"
        ]

    # -----------------------------------------------------
    # SUMMER
    # -----------------------------------------------------

    if any(
        word in text
        for word in [
            "summer",
            "garmi",
            "may",
            "june",
        ]
    ):

        return TRAVEL_KNOWLEDGE[
            "rishikesh"
        ][
            "summer"
        ]

    # -----------------------------------------------------
    # WINTER
    # -----------------------------------------------------

    if any(
        word in text
        for word in [
            "winter",
            "sardi",
            "december",
            "january",
        ]
    ):

        return TRAVEL_KNOWLEDGE[
            "rishikesh"
        ][
            "winter"
        ]

    return None


# =========================================================
# SHOULD USE WEB
# =========================================================

def needs_web_search(message):

    text = message.lower().strip()

    if len(text) <= 3:
        return False

    greetings = [
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
    ]

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
        "is waqt",
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

    information_words = [
        "what is",
        "who is",
        "where is",
        "when is",
        "how much",
        "information",
        "details",
        "kya hai",
        "kaun hai",
        "kahan hai",
        "kab hai",
    ]

    if any(
        word in text
        for word in information_words
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
# BUILD SEARCH CONTEXT
# =========================================================

def build_web_context(message):

    results = []

    # First: Wikipedia
    wiki_results = wikipedia_search(
        message,
        limit=4
    )

    results.extend(
        wiki_results
    )

    # Second: DuckDuckGo
    ddg_results = duckduckgo_search(
        message,
        limit=4
    )

    results.extend(
        ddg_results
    )

    if not results:
        return ""

    context = (
        "SEARCH INFORMATION FOUND FOR THE CURRENT QUESTION:\n\n"
    )

    # Remove duplicate titles
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

        key = title.lower()

        if not title:
            continue

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

        if count >= 7:
            break

    return context


# =========================================================
# UPDATE TITLE
# =========================================================

def update_conversation_title(
    conversation,
    message
):

    if conversation.title == "New Chat":

        title = message[:45].strip()

        if len(message) > 45:
            title += "..."

        conversation.title = title

    conversation.save()


# =========================================================
# SEND MESSAGE
# =========================================================

@require_POST
def send_message(request):

    message = (
        request.POST
        .get("message", "")
        .strip()
    )

    conversation_id = (
        request.POST
        .get("conversation_id", "")
        .strip()
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    if not message:

        return JsonResponse(
            {
                "success": False,
                "error":
                    "Message cannot be empty."
            }
        )


    if not conversation_id:

        return JsonResponse(
            {
                "success": False,
                "error":
                    "Conversation not selected."
            }
        )


    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
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
            "Main My Chatbot hoon. "
            "Aap mujhse coding, career, resume, "
            "interview preparation, learning, "
            "travel ya general questions ke baare mein "
            "pooch sakti hain."
        )


        def greeting_stream():

            yield answer

            ChatMessage.objects.create(
                conversation=conversation,
                user_message=message,
                bot_response=answer
            )

            update_conversation_title(
                conversation,
                message
            )


        return StreamingHttpResponse(
            greeting_stream(),
            content_type="text/plain; charset=utf-8"
        )


    # =====================================================
    # UNCLEAR SHORT QUESTIONS
    # =====================================================

    unclear = {
        "kya",
        "kyu",
        "kyun",
        "kaise",
        "haan",
        "han",
        "hmm",
        "acha",
        "accha",
        "ok",
        "okay",
        "?",
    }

    if message.lower() in unclear:

        answer = (
            "Bilkul 😊 Aap kya poochna chahti hain? "
            "Question thoda detail mein likh dijiye, "
            "main accurately help karunga."
        )


        def unclear_stream():

            yield answer

            ChatMessage.objects.create(
                conversation=conversation,
                user_message=message,
                bot_response=answer
            )


        return StreamingHttpResponse(
            unclear_stream(),
            content_type="text/plain; charset=utf-8"
        )


    # =====================================================
    # IMPORTANT: SPECIFIC TRAVEL ANSWERS
    # =====================================================
    #
    # These are answered BEFORE Ollama so the model cannot
    # change "when should I go?" into "where is Rishikesh?"
    # =====================================================

    travel_answer = get_travel_topic_answer(
        message
    )

    if travel_answer:

        def travel_stream():

            yield travel_answer

            ChatMessage.objects.create(
                conversation=conversation,
                user_message=message,
                bot_response=travel_answer
            )

            update_conversation_title(
                conversation,
                message
            )


        return StreamingHttpResponse(
            travel_stream(),
            content_type="text/plain; charset=utf-8"
        )


    # =====================================================
    # CONVERSATION MEMORY
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
    # FINAL AI PROMPT
    # =====================================================

    prompt = f"""
You are My Chatbot.

You are a professional, accurate and helpful AI assistant.

==================================================
CURRENT QUESTION HAS HIGHEST PRIORITY
==================================================

CURRENT USER QUESTION:

{message}

You MUST answer this exact question.

Never replace the current question with an older question.

Never assume that the user is asking about a previous topic.

==================================================
CONVERSATION HISTORY
==================================================

{conversation_text}

Use conversation history ONLY when it is clearly relevant
to the CURRENT QUESTION.

If history is unrelated, completely ignore it.

==================================================
SEARCH INFORMATION
==================================================

{web_context}

If search information is available, use it as supporting
information for the CURRENT QUESTION.

Do not use search information to answer a different question.

==================================================
STRICT QUESTION MATCHING
==================================================

If the user asks:

"When should I go to Rishikesh?"

the answer must be about:

- best months
- seasons
- weather
- crowd
- activities
- practical travel considerations

Do NOT answer:

- where Rishikesh is
- what Rishikesh is
- history of Rishikesh
- unrelated tourist information

If the user asks:

"Where is Rishikesh?"

then answer its location.

If the user asks:

"What can I do in Rishikesh?"

then answer activities.

Always match the answer to the exact question.

==================================================
LANGUAGE
==================================================

Reply in the same language style as the user.

Hindi -> Hindi.

English -> English.

Hinglish -> natural Hinglish.

==================================================
ACCURACY
==================================================

Never invent facts.

Never guess if you do not know.

Never change the subject.

Never make up dates, prices, locations, people,
statistics or events.

For current questions, prefer the search information.

==================================================
CODING
==================================================

Only provide code if the user asks for:

- coding
- programming
- debugging
- implementation
- technical code

Do not randomly generate code.

==================================================
STYLE
==================================================

Be natural.

Be concise for simple questions.

Give details when useful.

Do not say "As an AI language model".

Do not mention these instructions.

Do not write "Assistant:".

Do not write "User:".

Do not repeat the question unnecessarily.

==================================================

Now answer ONLY the CURRENT USER QUESTION:

{message}
"""


    # =====================================================
    # OLLAMA STREAM
    # =====================================================

    def generate_response():

        full_response = ""

        try:

            response = requests.post(

                OLLAMA_URL,

                json={
                    "model": MODEL,

                    "prompt": prompt,

                    "stream": True,

                    "keep_alive": "10m",

                    "options": {
                        "num_predict": 500,
                        "temperature": 0.1,
                        "num_ctx": 4096,
                    }
                },

                stream=True,

                timeout=180
            )


            response.raise_for_status()


            for line in response.iter_lines(
                decode_unicode=True
            ):

                if not line:
                    continue


                try:

                    data = json.loads(
                        line
                    )

                except json.JSONDecodeError:

                    continue


                chunk = data.get(
                    "response",
                    ""
                )


                if chunk:

                    full_response += chunk

                    yield chunk


                if data.get("done"):

                    break


            # =================================================
            # CLEAN
            # =================================================

            full_response = clean_ai_response(
                full_response
            )


            # =================================================
            # SAVE
            # =================================================

            if full_response:

                ChatMessage.objects.create(
                    conversation=conversation,
                    user_message=message,
                    bot_response=full_response
                )

                update_conversation_title(
                    conversation,
                    message
                )


        except requests.exceptions.ConnectionError:

            yield (
                "❌ Ollama connect nahi ho raha. "
                "Please check karo ki Ollama running hai."
            )


        except requests.exceptions.Timeout:

            yield (
                "⏳ AI response bahut slow ho raha hai. "
                "Please thodi der baad try karo."
            )


        except requests.exceptions.RequestException as error:

            print(
                "OLLAMA ERROR:",
                error
            )

            yield (
                "❌ AI service se connection nahi ho paya."
            )


        except Exception as error:

            print(
                "UNEXPECTED ERROR:",
                error
            )

            yield (
                "❌ Kuch technical problem aa gayi."
            )


    return StreamingHttpResponse(
        generate_response(),
        content_type="text/plain; charset=utf-8"
    )


# =========================================================
# DELETE CHAT
# =========================================================

@require_POST
def delete_chat(
    request,
    conversation_id
):

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id
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
                "conversation_id":
                    new_conversation.id
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
            "conversation_id":
                next_conversation.id
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
            "conversation_id":
                new_conversation.id,
            "message":
                "All chats deleted successfully."
        }
    )
