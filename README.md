# Library API
Restful Django project for managing a library.

## Features
- JWT Authentication
- Payments management (Stripe API)
- Borrowings management
- Book management
- Fines system
- Telegram notifications


## Installation
### Docker should be installed
```bash
git clone https://github.com/sashabryl/library-api.git
cd library-api
docker-compose build
docker-compose up
```

## Telegram notifications group
### To join the group go to https://t.me/library_notifications321

## Testing
### To run tests, type:
```bash
docker exec -it <id of the docker container with the app> python manage.py test
```

## Documentation
### To visit documentation go to
```bash
http://127.0.0.1:8000/api/doc/swagger/
```
