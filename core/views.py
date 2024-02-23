from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile, Post, LikePost, FollowersCount
from itertools import chain
import random

@login_required(login_url='signin')
def index(request):
    user_object = request.user
    user_profile = Profile.objects.get(pet=user_object)
    user_following_list = FollowersCount.objects.filter(follower=user_object.username).values_list('user', flat=True)

    feed = Post.objects.filter(user__in=user_following_list)

    all_users = User.objects.all()
    user_following_all = User.objects.filter(username__in=user_following_list)

    new_suggestions_list = all_users.exclude(username__in=user_following_all.values_list('username', flat=True))
    final_suggestions_list = new_suggestions_list.exclude(username=request.user.username)

    random.shuffle(final_suggestions_list)

    suggestions_username_profile_list = Profile.objects.filter(pet__in=final_suggestions_list)[:4]

    return render(request, 'index.html', {'user_profile': user_profile, 'posts': feed, 'suggestions_username_profile_list': suggestions_username_profile_list})

@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()

        return redirect('index')
    else:
        return redirect('index')

@login_required(login_url='signin')
def search(request):
    user_profile = Profile.objects.get(pet=request.user)

    if request.method == 'POST':
        username = request.POST['username']
        username_objects = User.objects.filter(username__icontains=username)
        username_profile_list = Profile.objects.filter(pet__in=username_objects)

    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})

@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter is None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.no_of_likes += 1
        post.save()
    else:
        like_filter.delete()
        post.no_of_likes -= 1
        post.save()

    return redirect('index')

@login_required(login_url='signin')
def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(pet=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = user_posts.count()

    follower = request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower, user=user).exists():
        button_text = 'Unfollow'
    else:
        button_text = 'Follow'

    user_followers = FollowersCount.objects.filter(user=pk).count()
    user_following = FollowersCount.objects.filter(follower=pk).count()

    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.user.username
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).exists():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()

    return redirect('profile', pk=user)

@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(pet=request.user)

    if request.method == 'POST':
        image = request.FILES.get('image')
        bio = request.POST['bio']
        location = request.POST['location']

        if image is not None:
            user_profile.profileImg = image

        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()

    return render(request, 'setting.html', {'user_profile': user_profile})

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                user_login = authenticate(username=username, password=password)
                login(request, user_login)

                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(pet=user_model)
                new_profile.save()

                return redirect('settings')
        else:
            messages.info(request, 'Password Not Matching')

    return render(request, 'signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')

    return render(request, 'signin.html')

@login_required(login_url='signin')
def logout_view(request):
    logout(request)
    return redirect('signin')