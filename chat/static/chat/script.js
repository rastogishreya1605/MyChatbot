
let currentConversationId =
    document.body.dataset.conversationId;

let isSending = false;


/* =========================================================
   CSRF
   ========================================================= */

function getCSRFToken() {

    const cookie = document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="));

    return cookie
        ? decodeURIComponent(cookie.split("=")[1])
        : "";
}

const messageInput =
    document.getElementById("message");

const chatArea =
    document.getElementById("chatArea");

const messages =
    document.getElementById("messages");

const sendButton =
    document.getElementById("sendButton");

const chatForm =
    document.getElementById("chatForm");



if (messageInput) {

    messageInput.addEventListener("input", () => {

        messageInput.style.height = "auto";

        messageInput.style.height =
            Math.min(messageInput.scrollHeight, 140) + "px";

    });

}
if (messageInput) {

    messageInput.addEventListener("keydown", (event) => {

        if (event.key === "Enter" && !event.shiftKey) {

            event.preventDefault();

            if (!isSending) {
                sendMessage(event);
            }

        }

    });

}



async function sendMessage(event) {

    if (event) {
        event.preventDefault();
    }

    if (isSending) {
        return;
    }

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }


    isSending = true;

    sendButton.disabled = true;


    /* Remove welcome */
    const welcome =
        document.getElementById("welcomeMessage");

    if (welcome) {
        welcome.remove();
    }


    /* Add user message */
    addUserMessage(message);


    /* Clear input */

    messageInput.value = "";

    messageInput.style.height = "auto";


    /* Typing indicator */

    const typingId =
        showTyping();


    scrollToBottom();


    try {

        const formData =
            new FormData();

        formData.append(
            "message",
            message
        );

        formData.append(
            "conversation_id",
            currentConversationId
        );


        const response =
            await fetch(
                "/send-message/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCSRFToken()
                    },

                    body: formData
                }
            );


        if (!response.ok) {

            throw new Error(
                "Server error: " +
                response.status
            );

        }


        removeTyping(typingId);


        /* Bot message */

        const botElements =
            createBotMessage();

        const botText =
            botElements.text;

        let fullResponse = "";


        if (response.body) {

            const reader =
                response.body.getReader();

            const decoder =
                new TextDecoder("utf-8");


            while (true) {

                const {
                    value,
                    done
                } = await reader.read();


                if (done) {
                    break;
                }


                const chunk =
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                fullResponse += chunk;


                botText.textContent =
                    cleanAssistantPrefix(
                        fullResponse
                    );


                scrollToBottom();
            }

        } else {

            fullResponse =
                await response.text();

            botText.textContent =
                cleanAssistantPrefix(
                    fullResponse
                );

        }


        botText.dataset.raw =
            cleanAssistantPrefix(
                fullResponse
            );


        updateCopyButton(
            botElements.copy,
            botText.dataset.raw
        );


        scrollToBottom();

    }

    catch (error) {

        removeTyping(typingId);

        console.error(
            "CHAT ERROR:",
            error
        );


        const errorElements =
            createBotMessage();


        errorElements.text.textContent =
            "❌ Sorry, response generate nahi ho paya. Please try again.";


        errorElements.text.dataset.raw =
            errorElements.text.textContent;

    }

    finally {

        isSending = false;

        sendButton.disabled = false;

        messageInput.focus();

    }

}


/* =========================================================
   CLEAN RESPONSE
   ========================================================= */

function cleanAssistantPrefix(text) {

    text = text || "";

    if (
        text
            .toLowerCase()
            .startsWith("assistant:")
    ) {

        return text
            .substring(10)
            .trim();

    }

    return text;

}


/* =========================================================
   USER MESSAGE
   ========================================================= */

function addUserMessage(text) {

    const row =
        document.createElement("div");

    row.className =
        "message-row user-row";


    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar user-avatar";

    avatar.textContent =
        "You";


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    const name =
        document.createElement("div");

    name.className =
        "message-name";

    name.textContent =
        "You";


    const message =
        document.createElement("div");

    message.className =
        "message-text";

    message.textContent =
        text;


    content.appendChild(name);

    content.appendChild(message);

    row.appendChild(avatar);

    row.appendChild(content);

    messages.appendChild(row);

}


/* =========================================================
   BOT MESSAGE
   ========================================================= */

function createBotMessage() {

    const row =
        document.createElement("div");

    row.className =
        "message-row bot-row";


    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar bot-avatar";

    avatar.textContent =
        "✦";


    const content =
        document.createElement("div");

    content.className =
        "message-content";


    const header =
        document.createElement("div");

    header.className =
        "message-header";


    const name =
        document.createElement("div");

    name.className =
        "message-name";

    name.textContent =
        "My Chatbot";


    const copy =
        document.createElement("button");

    copy.className =
        "copy-btn";

    copy.type =
        "button";

    copy.title =
        "Copy";

    copy.textContent =
        "⧉";


    const text =
        document.createElement("div");

    text.className =
        "message-text bot-text";

    text.dataset.raw =
        "";


    copy.onclick = function () {

        copyMessage(this);

    };


    header.appendChild(name);

    header.appendChild(copy);

    content.appendChild(header);

    content.appendChild(text);

    row.appendChild(avatar);

    row.appendChild(content);

    messages.appendChild(row);


    return {
        row,
        text,
        copy
    };

}


/* =========================================================
   TYPING INDICATOR
   ========================================================= */

function showTyping() {

    const id =
        "typing-" +
        Date.now();


    const row =
        document.createElement("div");

    row.className =
        "typing-row";

    row.id =
        id;


    const avatar =
        document.createElement("div");

    avatar.className =
        "message-avatar bot-avatar";

    avatar.textContent =
        "✦";


    const dots =
        document.createElement("div");

    dots.className =
        "typing-dots";


    for (let i = 0; i < 3; i++) {

        const dot =
            document.createElement("span");

        dots.appendChild(dot);

    }


    row.appendChild(avatar);

    row.appendChild(dots);

    messages.appendChild(row);


    return id;

}


function removeTyping(id) {

    const element =
        document.getElementById(id);

    if (element) {
        element.remove();
    }

}


/* =========================================================
   COPY
   ========================================================= */

async function copyMessage(button) {

    const message =
        button
            .closest(".message-content")
            .querySelector(".bot-text");


    const text =
        message.dataset.raw ||
        message.innerText;


    try {

        await navigator.clipboard.writeText(text);

        const old =
            button.textContent;

        button.textContent =
            "✓";


        setTimeout(() => {

            button.textContent =
                old;

        }, 1200);

    }

    catch (error) {

        console.error(
            "Copy failed:",
            error
        );

    }

}


function updateCopyButton(
    button,
    text
) {

    button.dataset.copy =
        text;

}


/* =========================================================
   SUGGESTIONS
   ========================================================= */

function useSuggestion(text) {

    if (!messageInput) {
        return;
    }

    messageInput.value =
        text;

    messageInput.dispatchEvent(
        new Event("input")
    );

    messageInput.focus();

    sendMessage();

}


/* =========================================================
   NEW CHAT
   ========================================================= */

async function newChat() {

    if (isSending) {
        return;
    }


    try {

        const response =
            await fetch(
                "/new-chat/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCSRFToken()
                    }
                }
            );


        const data =
            await response.json();


        if (data.success) {

            window.location.href =
                "/conversation/" +
                data.conversation_id +
                "/";

        }

    }

    catch (error) {

        console.error(
            "NEW CHAT ERROR:",
            error
        );

    }

}


/* =========================================================
   OPEN CONVERSATION
   ========================================================= */

function openConversation(id) {

    if (isSending) {
        return;
    }

    window.location.href =
        "/conversation/" +
        id +
        "/";

}


/* =========================================================
   DELETE CHAT
   ========================================================= */

async function deleteConversation(
    event,
    id
) {

    event.stopPropagation();


    if (isSending) {
        return;
    }


    const confirmed =
        confirm(
            "Delete this conversation?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                "/delete-chat/" +
                id +
                "/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCSRFToken()
                    }
                }
            );


        const data =
            await response.json();


        if (data.success) {

            window.location.href =
                "/conversation/" +
                data.conversation_id +
                "/";

        }

    }

    catch (error) {

        console.error(
            "DELETE ERROR:",
            error
        );

    }

}


/* =========================================================
   DELETE ALL
   ========================================================= */

async function deleteAllChats() {

    if (isSending) {
        return;
    }


    const confirmed =
        confirm(
            "Are you sure you want to delete all chats?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                "/clear-chat/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            getCSRFToken()
                    }
                }
            );


        const data =
            await response.json();


        if (data.success) {

            window.location.href =
                "/conversation/" +
                data.conversation_id +
                "/";

        }

    }

    catch (error) {

        console.error(
            "CLEAR ERROR:",
            error
        );

    }

}


/* =========================================================
   CHAT SEARCH
   ========================================================= */

const chatSearch =
    document.getElementById(
        "chatSearch"
    );


if (chatSearch) {

    chatSearch.addEventListener(
        "input",
        function () {

            const query =
                this.value
                    .toLowerCase()
                    .trim();


            document
                .querySelectorAll(
                    ".conversation-item"
                )
                .forEach(item => {

                    const title =
                        item.dataset.title ||
                        "";


                    if (
                        title.includes(query)
                    ) {

                        item.style.display =
                            "flex";

                    }

                    else {

                        item.style.display =
                            "none";

                    }

                });

        }
    );

}


/* =========================================================
   THEME
   ========================================================= */

function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );


    const dark =
        document.body.classList.contains(
            "dark"
        );


    localStorage.setItem(
        "chatbot-theme",
        dark
            ? "dark"
            : "light"
    );


    updateThemeIcon();

}


function updateThemeIcon() {

    const button =
        document.getElementById(
            "themeButton"
        );


    if (!button) {
        return;
    }


    const dark =
        document.body.classList.contains(
            "dark"
        );


    button.textContent =
        dark
            ? "☀"
            : "☾";

}


/* Load saved theme */

(function loadTheme() {

    const saved =
        localStorage.getItem(
            "chatbot-theme"
        );


    if (saved === "dark") {

        document.body.classList.add(
            "dark"
        );

    }


    updateThemeIcon();

})();


/* =========================================================
   MOBILE SIDEBAR
   ========================================================= */

function toggleSidebar() {

    const sidebar =
        document.getElementById(
            "sidebar"
        );

    const overlay =
        document.getElementById(
            "sidebarOverlay"
        );


    sidebar.classList.toggle(
        "open"
    );

    overlay.classList.toggle(
        "show"
    );

}


/* Close mobile sidebar after opening chat */

document
    .querySelectorAll(
        ".conversation-main"
    )
    .forEach(item => {

        item.addEventListener(
            "click",
            () => {

                if (
                    window.innerWidth <= 850
                ) {

                    toggleSidebar();

                }

            }
        );

    });


/* =========================================================
   AUTO SCROLL
   ========================================================= */

function scrollToBottom() {

    requestAnimationFrame(() => {

        chatArea.scrollTop =
            chatArea.scrollHeight;

    });

}


/* Initial scroll */

window.addEventListener(
    "load",
    () => {

        scrollToBottom();

        if (messageInput) {
            messageInput.focus();
        }

    }
);

