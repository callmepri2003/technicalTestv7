from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    FREQUENCY_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('FORTNIGHTLY', 'Fortnightly'),
        ('MONTHLY', 'Monthly'),
        ('CUSTOM', 'Custom'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    preferred_shopping_day = models.IntegerField(
        blank=True, null=True, choices=[(i, str(i)) for i in range(7)],
        help_text="0=Monday, 6=Sunday" # 0: Monday, 1: Tuesday, ..., 6: Sunday
    )
    preferred_shopping_frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default='WEEKLY'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

# Signal to automatically create a UserProfile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Signal to save the UserProfile when the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # This ensures that if the User object is saved, its associated UserProfile is also saved.
    # It's important to check if the profile already exists to avoid errors on initial creation.
    if hasattr(instance, 'profile'):
        instance.profile.save()