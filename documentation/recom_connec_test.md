# API Test Reference
Base URL: `https://vanijyaa-backend.onrender.com`

---

## Recommendations

### Get recommendations for a user
```
GET https://vanijyaa-backend.onrender.com/recommendations/1
```

### Search with custom payload (no user_id needed)
```
POST https://vanijyaa-backend.onrender.com/recommendations/search

{
    "commodity": ["rice", "cotton"],
    "role": "trader",
    "latitude_raw": 19.076,
    "longitude_raw": 72.877,
    "qty_min_mt": 100,
    "qty_max_mt": 500
}
```

### Refresh a user's stored vector
```
GET https://vanijyaa-backend.onrender.com/recommendations/1/refresh
```

---

## Connections — Follow

### Follow a user
```
POST https://vanijyaa-backend.onrender.com/connections/follow/2

{
    "me": 1
}
```

### Unfollow a user
```
DELETE https://vanijyaa-backend.onrender.com/connections/follow/2?me=1
```

### Get followers of a user
```
GET https://vanijyaa-backend.onrender.com/connections/followers/2
```

### Get everyone a user follows
```
GET https://vanijyaa-backend.onrender.com/connections/following/1
```

### Check follow status
```
GET https://vanijyaa-backend.onrender.com/connections/follow/status/2?me=1
```

---

## Connections — Message Requests

### Send a message request
```
POST https://vanijyaa-backend.onrender.com/connections/message-request/2

{
    "me": 1
}
```

### Withdraw a pending message request
```
DELETE https://vanijyaa-backend.onrender.com/connections/message-request/2?me=1
```

### Accept a message request
```
PATCH https://vanijyaa-backend.onrender.com/connections/message-request/1/accept

{
    "me": 2
}
```

### Decline a message request
```
PATCH https://vanijyaa-backend.onrender.com/connections/message-request/1/decline

{
    "me": 2
}
```

### My pending inbox (requests received)
```
GET https://vanijyaa-backend.onrender.com/connections/message-requests/received?me=2
```

### Requests I have sent
```
GET https://vanijyaa-backend.onrender.com/connections/message-requests/sent?me=1
```

---

## Connections — Search

### Search with text query
```
GET https://vanijyaa-backend.onrender.com/connections/search?me=1&q=abhishek
```

### Search with filters
```
GET https://vanijyaa-backend.onrender.com/connections/search?me=1&role=exporter&commodity=rice&city=pune
```

### Fuzzy suggestions (typo handling)
```
GET https://vanijyaa-backend.onrender.com/connections/search/suggestions?q=xpotar
```