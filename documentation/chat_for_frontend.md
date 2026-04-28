1. App startup — connect WebSocket immediately
The moment the user logs in, open the WebSocket. Don't wait for the chat screen.


// as soon as you have user_id after login
const ws = new WebSocket(`ws://host/ws/chat/${user_id}`)

ws.onmessage = (event) => {
  const { event: type, data } = JSON.parse(event.data)

  if (type === "new_message") {
    handleIncomingMessage(data.conversation_id, data.message)
  }
}
Keep this single WebSocket alive for the entire app session. Reconnect on disconnect with exponential backoff.

2. Conversation list screen

GET /api/v1/chat/{user_id}/conversations?page=1&per_page=20
Do this once on screen open. Then never poll — the WebSocket tells you when to update.


Response shape per conversation:
{
  id, status,           ← "requested" | "active" | "blocked"
  participant: { user_id, name, is_verified },
  last_message: { body, sent_at, sender_id },
  unread_count,
  is_muted
}
When WebSocket fires new_message:

Find the conversation in your local list by conversation_id
Update last_message preview
If sender is NOT the current user → increment unread_count
Move that conversation to top (sort by last message sent_at)
3. Opening a chat screen — load history

GET /api/v1/chat/{user_id}/conversations/{conv_id}/messages?limit=50
Do NOT wait for this before showing the screen. Show a skeleton, load in background, then fill.


Response:
{
  messages: [...],    ← ordered newest → oldest
  has_more: bool,
  oldest_timestamp: "2024-..."
}
Reverse the array before rendering (you want oldest at top, newest at bottom). After rendering, immediately mark read:


POST /api/v1/chat/{user_id}/conversations/{conv_id}/read
Pagination (scroll to top): when user scrolls to top and has_more is true:


GET /messages?before={oldest_timestamp}&limit=50
Prepend results to the list.

4. Sending a message — optimistic UI
Never wait for the HTTP response before showing the message. Show it immediately, then confirm.


Step 1: User presses send
  → generate a temp_id (e.g. `temp_${Date.now()}`)
  → append message to UI with status: "sending" (grey tick)

Step 2: POST /api/v1/chat/{user_id}/conversations/{conv_id}/messages
  body: { body: "hello", message_type: "text" }

Step 3a: HTTP 201 → replace temp_id with real id from response, status: "sent" (single tick)
Step 3b: HTTP 403 → show error on that message ("request not accepted yet")
Step 3c: Network error → show retry button on that message
The receiver gets it via WebSocket before your HTTP 201 even comes back.

5. Receiving a message — WebSocket handler

function handleIncomingMessage(conversation_id, message) {
  if (currentOpenConvId === conversation_id) {
    // User is looking at this chat right now
    appendMessageToView(message)
    markRead(conversation_id)          // POST /read
    resetUnreadCount(conversation_id)  // local state
  } else {
    // User is somewhere else in the app
    incrementUnreadBadge(conversation_id)
    updateLastMessagePreview(conversation_id, message)
    showPushNotification(message)
  }
}
6. Chat request flow (the receiver side)
When you open a conversation with status: "requested" and initiator_id !== your_user_id:


Show:  [Accept]  [Decline]  buttons — do NOT show message input

POST /api/v1/chat/{user_id}/conversations/{conv_id}/accept
  → response: { conversation: { status: "active", ... } }
  → hide buttons, show message input, both can now type

POST /api/v1/chat/{user_id}/conversations/{conv_id}/decline
  → response: { conversation: { status: "blocked", ... } }
  → show "Request declined" state
If status: "requested" and initiator_id === your_user_id (you sent the request):


Show: message input (you can still send)
Show: "Waiting for X to accept" banner
Hide: the accept/decline buttons
7. Starting a new chat

POST /api/v1/chat/{user_id}/conversations
body: { participant_id: "uuid-of-other-user", message: "first message text" }

Response: { conversation: {...}, message: {...}, created: true/false }
This creates the conversation AND sends the first message in one shot. Navigate to the chat screen using the returned conversation.id.

The complete screen lifecycle

App opens
  └─ connect WebSocket (/ws/chat/{user_id})

Conversation List
  └─ GET /conversations            (load once)
  └─ WebSocket new_message         (update in real-time)

Chat Screen opens
  ├─ GET /conversations/{id}/messages   (load history)
  ├─ POST /conversations/{id}/read      (mark read)
  └─ WebSocket new_message              (append live)

User sends
  ├─ show optimistically
  ├─ POST /conversations/{id}/messages
  └─ confirm or show error

User accepts request
  └─ POST /conversations/{id}/accept

App goes to background
  └─ keep WebSocket alive (or reconnect on foreground)
  └─ show push notifications for missed new_message events
The key rules:

1 WebSocket for the whole app — not per-screen
Optimistic send — show message before HTTP confirms
Never poll — list screen updates via WebSocket only
Mark read immediately on screen open and on each incoming message while the screen is open