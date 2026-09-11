// =========================================================
// MY CHATBOT - FINAL SCRIPT
// =========================================================

let currentConversationId =
  document.body.dataset.conversationId || null;

let isSending = false;


// =========================================================
// DOM ELEMENTS
// =========================================================

const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("sendButton");
const messagesContainer = document.getElementById("messages");
const chatArea = document.getElementById("chatArea");
const conversationList = document.getElementById("conversationList");
const chatSearch = document.getElementById("chatSearch");
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const themeButton = document.getElementById("themeButton");


// =========================================================
// CSRF TOKEN
// =========================================================

function getCSRFToken() {
  const cookieValue = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));

  if (!cookieValue) {
    return "";
  }

  return decodeURIComponent(cookieValue.split("=")[1]);
}


// =========================================================
// TEXTAREA AUTO RESIZE
// =========================================================

function autoResizeTextarea() {
  if (!messageInput) return;

  messageInput.style.height = "auto";

  const maxHeight = 180;

  messageInput.style.height =
    Math.min(messageInput.scrollHeight, maxHeight) + "px";
}

if (messageInput) {
  messageInput.addEventListener("input", autoResizeTextarea);
}


// =========================================================
// ENTER KEY
// =========================================================

if (messageInput) {
  messageInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (!isSending) {
        sendMessage(event);
      }
    }
  });
}


// =========================================================
// SEND MESSAGE
// =========================================================

async function sendMessage(event) {
  if (event) {
    event.preventDefault();
  }

  if (isSending) {
    return;
  }

  if (!messageInput) {
    return;
  }

  const message = messageInput.value.trim();

  if (!message) {
    return;
  }

  isSending = true;

  if (sendButton) {
    sendButton.disabled = true;
    sendButton.classList.add("loading");
  }

  // Remove welcome screen
  const welcomeMessage = document.getElementById("welcomeMessage");

  if (welcomeMessage) {
    welcomeMessage.remove();
  }

  // Add user's message
  addUserMessage(message);

  // Clear input
  messageInput.value = "";
  autoResizeTextarea();

  // Show typing
  const typingElement = showTypingIndicator();

  try {
    const formData = new FormData();

    formData.append("message", message);

    if (currentConversationId) {
      formData.append(
        "conversation_id",
        currentConversationId
      );
    }

    const csrfToken = getCSRFToken();

    console.log("Sending message...");
    console.log("Conversation ID:", currentConversationId);

    const response = await fetch("/send-message/", {
      method: "POST",

      headers: {
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest"
      },

      body: formData,

      credentials: "same-origin"
    });


    // =====================================================
    // HTTP ERROR
    // =====================================================

    if (!response.ok) {
      const errorText = await response.text();

      console.error(
        "SERVER ERROR:",
        response.status,
        errorText
      );

      throw new Error(
        "Server returned HTTP " + response.status
      );
    }


    // =====================================================
    // GET COMPLETE RESPONSE
    // =====================================================

    const responseText = await response.text();

    console.log("CHATBOT RESPONSE:");
    console.log(responseText);


    // =====================================================
    // REMOVE TYPING
    // =====================================================

    if (typingElement) {
      typingElement.remove();
    }


    // =====================================================
    // EMPTY RESPONSE
    // =====================================================

    if (!responseText || !responseText.trim()) {
      throw new Error("Empty response received from server.");
    }


    // =====================================================
    // CREATE BOT MESSAGE
    // =====================================================

    const botMessage = createBotMessage();

    const botText =
      botMessage.querySelector(".bot-text");

    if (botText) {
      botText.textContent =
        cleanAssistantPrefix(responseText);
    }


    // =====================================================
    // UPDATE CONVERSATION ID
    // =====================================================

    const returnedConversationId =
      response.headers.get("X-Conversation-ID");

    if (returnedConversationId) {
      currentConversationId = returnedConversationId;

      document.body.dataset.conversationId =
        returnedConversationId;
    }


    // =====================================================
    // REFRESH CHAT LIST
    // =====================================================

    setTimeout(() => {
      refreshConversationList();
    }, 300);


    scrollToBottom();

  } catch (error) {

    console.error("CHAT ERROR:", error);

    if (typingElement) {
      typingElement.remove();
    }

    showError(
      "Sorry, response generate nahi ho paya. Please try again."
    );

  } finally {

    isSending = false;

    if (sendButton) {
      sendButton.disabled = false;
      sendButton.classList.remove("loading");
    }

    messageInput.focus();
  }
}


// =========================================================
// CLEAN ASSISTANT PREFIX
// =========================================================

function cleanAssistantPrefix(text) {
  if (!text) {
    return "";
  }

  let cleaned = text.trim();

  cleaned = cleaned.replace(
    /^(assistant|ai|bot|my chatbot)\s*:\s*/i,
    ""
  );

  return cleaned.trim();
}


// =========================================================
// ADD USER MESSAGE
// =========================================================

function addUserMessage(message) {
  if (!messagesContainer) {
    return;
  }

  const row = document.createElement("div");

  row.className =
    "message-row user-row";

  const avatar =
    document.createElement("div");

  avatar.className =
    "message-avatar user-avatar";

  avatar.textContent = "You";

  const content =
    document.createElement("div");

  content.className =
    "message-content";

  const name =
    document.createElement("div");

  name.className =
    "message-name";

  name.textContent = "You";

  const text =
    document.createElement("div");

  text.className =
    "message-text";

  text.textContent = message;

  content.appendChild(name);
  content.appendChild(text);

  row.appendChild(avatar);
  row.appendChild(content);

  messagesContainer.appendChild(row);

  scrollToBottom();
}


// =========================================================
// CREATE BOT MESSAGE
// =========================================================

function createBotMessage() {
  const row =
    document.createElement("div");

  row.className =
    "message-row bot-row";

  const avatar =
    document.createElement("div");

  avatar.className =
    "message-avatar bot-avatar";

  avatar.textContent = "✦";

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

  const copyButton =
    document.createElement("button");

  copyButton.className =
    "copy-btn";

  copyButton.type =
    "button";

  copyButton.title =
    "Copy";

  copyButton.textContent =
    "⧉";

  copyButton.onclick =
    function () {
      copyMessage(copyButton);
    };

  const text =
    document.createElement("div");

  text.className =
    "message-text bot-text";

  header.appendChild(name);
  header.appendChild(copyButton);

  content.appendChild(header);
  content.appendChild(text);

  row.appendChild(avatar);
  row.appendChild(content);

  messagesContainer.appendChild(row);

  scrollToBottom();

  return row;
}


// =========================================================
// TYPING INDICATOR
// =========================================================

function showTypingIndicator() {
  if (!messagesContainer) {
    return null;
  }

  const row =
    document.createElement("div");

  row.className =
    "message-row bot-row typing-row";

  row.innerHTML = `
    <div class="message-avatar bot-avatar">✦</div>

    <div class="message-content">
      <div class="message-header">
        <div class="message-name">My Chatbot</div>
      </div>

      <div class="message-text bot-text">
        <span class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </span>
      </div>
    </div>
  `;

  messagesContainer.appendChild(row);

  scrollToBottom();

  return row;
}


// =========================================================
// SHOW ERROR
// =========================================================

function showError(message) {
  if (!messagesContainer) {
    return;
  }

  const row =
    document.createElement("div");

  row.className =
    "message-row bot-row error-row";

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

  const name =
    document.createElement("div");

  name.className =
    "message-name";

  name.textContent =
    "My Chatbot";

  const text =
    document.createElement("div");

  text.className =
    "message-text bot-text";

  text.textContent =
    "❌ " + message;

  content.appendChild(name);
  content.appendChild(text);

  row.appendChild(avatar);
  row.appendChild(content);

  messagesContainer.appendChild(row);

  scrollToBottom();
}


// =========================================================
// COPY MESSAGE
// =========================================================

async function copyMessage(button) {
  if (!button) {
    return;
  }

  const content =
    button.closest(".message-content");

  if (!content) {
    return;
  }

  const textElement =
    content.querySelector(".bot-text");

  if (!textElement) {
    return;
  }

  const text =
    textElement.innerText.trim();

  if (!text) {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);

    const oldText =
      button.textContent;

    button.textContent =
      "✓";

    setTimeout(() => {
      button.textContent =
        oldText;
    }, 1200);

  } catch (error) {

    console.error(
      "Copy failed:",
      error
    );

    // Fallback
    const textarea =
      document.createElement("textarea");

    textarea.value = text;

    document.body.appendChild(textarea);

    textarea.select();

    document.execCommand("copy");

    textarea.remove();

    button.textContent =
      "✓";

    setTimeout(() => {
      button.textContent =
        "⧉";
    }, 1200);
  }
}


// =========================================================
// SUGGESTION
// =========================================================

function useSuggestion(text) {
  if (!messageInput) {
    return;
  }

  messageInput.value =
    text;

  autoResizeTextarea();

  messageInput.focus();

  setTimeout(() => {
    if (!isSending) {
      sendMessage();
    }
  }, 100);
}


// =========================================================
// NEW CHAT
// =========================================================

async function newChat() {
  try {

    const response =
      await fetch("/new-chat/", {
        method: "POST",

        headers: {
          "X-CSRFToken": getCSRFToken(),
          "X-Requested-With": "XMLHttpRequest"
        },

        credentials: "same-origin"
      });


    if (!response.ok) {
      throw new Error(
        "Could not create new chat."
      );
    }


    const data =
      await response.json();

    console.log(
      "NEW CHAT:",
      data
    );


    if (data.conversation_id) {

      currentConversationId =
        data.conversation_id;

      document.body.dataset.conversationId =
        data.conversation_id;
    }


    window.location.reload();

  } catch (error) {

    console.error(
      "New chat error:",
      error
    );

    window.location.href =
      "/";
  }
}


// =========================================================
// OPEN CONVERSATION
// =========================================================

function openConversation(conversationId) {
  if (!conversationId) {
    return;
  }

  window.location.href =
    "/?conversation=" +
    encodeURIComponent(conversationId);
}


// =========================================================
// DELETE CONVERSATION
// =========================================================

async function deleteConversation(
  event,
  conversationId
) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }

  if (!conversationId) {
    return;
  }

  const confirmed =
    confirm(
      "Are you sure you want to delete this chat?"
    );

  if (!confirmed) {
    return;
  }

  try {

    const response =
      await fetch(
        "/delete-conversation/" +
          conversationId +
          "/",
        {
          method: "POST",

          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With":
              "XMLHttpRequest"
          },

          credentials: "same-origin"
        }
      );


    if (!response.ok) {
      throw new Error(
        "Delete failed."
      );
    }


    const item =
      document.querySelector(
        `.conversation-item[data-conversation-id="${conversationId}"]`
      );

    if (item) {
      item.remove();
    }


    if (
      String(currentConversationId) ===
      String(conversationId)
    ) {
      window.location.href = "/";
    }

  } catch (error) {

    console.error(
      "Delete conversation error:",
      error
    );

    alert(
      "Chat delete nahi ho payi."
    );
  }
}


// =========================================================
// DELETE ALL CHATS
// =========================================================

async function deleteAllChats() {
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
        "/delete-all-chats/",
        {
          method: "POST",

          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With":
              "XMLHttpRequest"
          },

          credentials: "same-origin"
        }
      );


    if (!response.ok) {
      throw new Error(
        "Delete all chats failed."
      );
    }


    window.location.href =
      "/";

  } catch (error) {

    console.error(
      "Delete all chats error:",
      error
    );

    alert(
      "Chats delete nahi ho payi."
    );
  }
}


// =========================================================
// REFRESH CONVERSATION LIST
// =========================================================

async function refreshConversationList() {
  try {

    const response =
      await fetch(
        window.location.href,
        {
          method: "GET",
          credentials: "same-origin"
        }
      );

    if (!response.ok) {
      return;
    }

    const html =
      await response.text();

    const parser =
      new DOMParser();

    const documentHTML =
      parser.parseFromString(
        html,
        "text/html"
      );

    const newList =
      documentHTML.querySelector(
        "#conversationList"
      );

    if (!newList || !conversationList) {
      return;
    }

    conversationList.innerHTML =
      newList.innerHTML;

  } catch (error) {

    console.error(
      "Conversation refresh error:",
      error
    );
  }
}


// =========================================================
// CHAT SEARCH
// =========================================================

if (chatSearch) {
  chatSearch.addEventListener(
    "input",
    function () {

      const searchValue =
        this.value
          .trim()
          .toLowerCase();

      const items =
        document.querySelectorAll(
          ".conversation-item"
        );


      items.forEach((item) => {

        const title =
          item.dataset.title || "";

        if (
          !searchValue ||
          title.includes(searchValue)
        ) {
          item.style.display =
            "flex";
        } else {
          item.style.display =
            "none";
        }

      });
    }
  );
}


// =========================================================
// THEME
// =========================================================

function toggleTheme() {
  const currentTheme =
    document.documentElement
      .getAttribute("data-theme");

  const newTheme =
    currentTheme === "dark"
      ? "light"
      : "dark";

  document.documentElement.setAttribute(
    "data-theme",
    newTheme
  );

  localStorage.setItem(
    "chatbot-theme",
    newTheme
  );

  updateThemeButton(newTheme);
}


// =========================================================
// UPDATE THEME BUTTON
// =========================================================

function updateThemeButton(theme) {
  if (!themeButton) {
    return;
  }

  if (theme === "dark") {
    themeButton.textContent =
      "☀";

    themeButton.title =
      "Switch to light theme";

  } else {

    themeButton.textContent =
      "☾";

    themeButton.title =
      "Switch to dark theme";
  }
}


// =========================================================
// LOAD THEME
// =========================================================

function loadTheme() {
  const savedTheme =
    localStorage.getItem(
      "chatbot-theme"
    );

  if (savedTheme) {

    document.documentElement.setAttribute(
      "data-theme",
      savedTheme
    );

    updateThemeButton(
      savedTheme
    );

    return;
  }


  const prefersDark =
    window.matchMedia &&
    window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;


  if (prefersDark) {

    document.documentElement.setAttribute(
      "data-theme",
      "dark"
    );

    updateThemeButton(
      "dark"
    );

  } else {

    document.documentElement.setAttribute(
      "data-theme",
      "light"
    );

    updateThemeButton(
      "light"
    );
  }
}


// =========================================================
// MOBILE SIDEBAR
// =========================================================

function toggleSidebar() {
  if (!sidebar) {
    return;
  }

  sidebar.classList.toggle(
    "open"
  );

  if (sidebarOverlay) {
    sidebarOverlay.classList.toggle(
      "active"
    );
  }
}


// =========================================================
// CLOSE SIDEBAR WHEN CONVERSATION OPENED
// =========================================================

document.addEventListener(
  "click",
  function (event) {

    const conversation =
      event.target.closest(
        ".conversation-main"
      );

    if (
      conversation &&
      window.innerWidth <= 768
    ) {
      if (sidebar) {
        sidebar.classList.remove(
          "open"
        );
      }

      if (sidebarOverlay) {
        sidebarOverlay.classList.remove(
          "active"
        );
      }
    }
  }
);


// =========================================================
// SCROLL TO BOTTOM
// =========================================================

function scrollToBottom() {
  if (!chatArea) {
    return;
  }

  requestAnimationFrame(() => {

    chatArea.scrollTop =
      chatArea.scrollHeight;

    window.scrollTo(
      0,
      document.body.scrollHeight
    );

  });
}


// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener(
  "DOMContentLoaded",
  function () {

    loadTheme();

    autoResizeTextarea();

    setTimeout(() => {
      scrollToBottom();
    }, 100);

    if (messageInput) {
      messageInput.focus();
    }

  }
);


// =========================================================
// EXPOSE FUNCTIONS TO HTML
// =========================================================

window.sendMessage =
  sendMessage;

window.newChat =
  newChat;

window.openConversation =
  openConversation;

window.deleteConversation =
  deleteConversation;

window.deleteAllChats =
  deleteAllChats;

window.copyMessage =
  copyMessage;

window.useSuggestion =
  useSuggestion;

window.toggleTheme =
  toggleTheme;

window.toggleSidebar =
  toggleSidebar;