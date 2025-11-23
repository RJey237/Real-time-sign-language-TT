from django.db import models
from django.contrib.auth.models import User
import secrets
import string


def generate_random_id(length=8):
	alphabet = string.ascii_uppercase + string.digits
	return ''.join(secrets.choice(alphabet) for _ in range(length))


class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	random_id = models.CharField(max_length=16, unique=True, db_index=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		if not self.random_id:
			# Ensure uniqueness
			rid = generate_random_id()
			while UserProfile.objects.filter(random_id=rid).exists():
				rid = generate_random_id()
			self.random_id = rid
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.user.username} ({self.random_id})"


class ChatMessage(models.Model):
	room = models.CharField(max_length=64, db_index=True)
	sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

