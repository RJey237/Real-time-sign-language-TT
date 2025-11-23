from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
import json

from .models import UserProfile


def json_body(request):
	try:
		return json.loads(request.body.decode('utf-8')) if request.body else {}
	except Exception:
		return {}


@csrf_exempt
@transaction.atomic
def register_view(request):
	try:
		if request.method != 'POST':
			return JsonResponse({'error': 'Method not allowed'}, status=405)
		
		# Parse JSON body
		try:
			data = json.loads(request.body.decode('utf-8'))
		except:
			print(f'[AUTH] Register: Failed to parse JSON body: {request.body}')
			return JsonResponse({'error': 'Invalid JSON'}, status=400)
		
		username = data.get('username', '').strip()
		password = data.get('password', '').strip()
		
		print(f'[AUTH] Register attempt: username={username}, password_len={len(password)}')
		
		if not username or not password:
			return JsonResponse({'error': 'username and password required'}, status=400)
		
		if User.objects.filter(username=username).exists():
			return JsonResponse({'error': 'username already taken'}, status=400)
		
		user = User.objects.create_user(username=username, password=password)
		profile, _ = UserProfile.objects.get_or_create(user=user)
		
		print(f'[AUTH] Register success: {username} -> {profile.random_id}')
		return JsonResponse({
			'ok': True,
			'authenticated': True,
			'username': user.username,
			'random_id': profile.random_id
		})
	except Exception as e:
		print(f'[AUTH] Register error: {str(e)}')
		import traceback
		traceback.print_exc()
		return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def login_view(request):
	try:
		if request.method != 'POST':
			return JsonResponse({'error': 'Method not allowed'}, status=405)
		data = json_body(request)
		username = data.get('username', '').strip()
		password = data.get('password', '').strip()
		
		user = authenticate(request, username=username, password=password)
		if user is None:
			print(f'[AUTH] Login failed for {username}: invalid credentials')
			return JsonResponse({'error': 'invalid credentials'}, status=401)
		
		login(request, user)
		profile, _ = UserProfile.objects.get_or_create(user=user)
		
		print(f'[AUTH] Login success: {username} -> {profile.random_id}')
		return JsonResponse({
			'ok': True,
			'authenticated': True,
			'username': user.username,
			'random_id': profile.random_id
		})
	except Exception as e:
		print(f'[AUTH] Login error: {str(e)}')
		return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def logout_view(request):
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)
	if request.user.is_authenticated:
		logout(request)
	return JsonResponse({'ok': True})


@csrf_exempt
def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False})
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return JsonResponse({'authenticated': True, 'username': request.user.username, 'random_id': profile.random_id})
def user_lookup_view(request, random_id: str):
	try:
		profile = UserProfile.objects.get(random_id=random_id)
		return JsonResponse({'found': True, 'username': profile.user.username, 'random_id': profile.random_id})
	except UserProfile.DoesNotExist:
		return JsonResponse({'found': False}, status=404)
