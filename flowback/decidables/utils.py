from flowback.user.models import User

def add_users_to_decidable_chat(decidable):
    user = User.objects.filter(
        is_active=True,
        
    )