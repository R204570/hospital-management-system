from django.apps import AppConfig
from django.contrib.auth import user_logged_in


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        # We no longer need the MongoDB-specific signal handling
        # Since we're using Django's default database, we can just use Django's default update_last_login
        pass 