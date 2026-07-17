# System Diagram (architecture)

```
[Browser]
   |  HTML/CSS/JS
   v
[Flask API :5000]
   |-- /api/auth      (JWT: register, login)
   |-- /api/restaurants (JWT required)
   v
[SQLite Database]
   |-- users
   |-- restaurants
```

Replace with a drawn sequence/architecture diagram image for the presentation.
