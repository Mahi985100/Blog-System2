
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Blog, Comment, Category, Profile, Bookmark
from .forms import RegisterForm, BlogForm, CommentForm, ProfileForm, UserForm

def home(request):
    search = request.GET.get('search')
    category_id = request.GET.get('category')
    
    blogs = Blog.objects.select_related('category').prefetch_related('authors').order_by('-created_at')
    categories = Category.objects.all()
    
    # Trending Blogs Logic: Most liked or most viewed recently
    trending_blogs = Blog.objects.select_related('category').prefetch_related('authors').filter(is_trending=True) | Blog.objects.select_related('category').prefetch_related('authors').order_by('-views_count', '-created_at')[:4]
    trending_blogs = trending_blogs.distinct()[:4]

    if search:
        blogs = blogs.filter(Q(title__icontains=search) | Q(content__icontains=search))
    
    if category_id:
        blogs = blogs.filter(category_id=category_id)

    paginator = Paginator(blogs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home.html', {
        'page_obj': page_obj,
        'categories': categories,
        'trending_blogs': trending_blogs,
        'selected_category': int(category_id) if category_id else None
    })

def detail(request, id):
    blog = get_object_or_404(Blog.objects.select_related('category').prefetch_related('authors', 'likes'), id=id)
    # Increment view count
    blog.views_count += 1
    blog.save()
    
    comments = Comment.objects.filter(blog=blog).order_by('-created_at')
    is_liked = False
    is_bookmarked = False
    
    if request.user.is_authenticated:
        if blog.likes.filter(id=request.user.id).exists():
            is_liked = True
        if Bookmark.objects.filter(user=request.user, blog=blog).exists():
            is_bookmarked = True

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.user = request.user
            comment.save()
            return redirect('detail', id=id)
    else:
        form = CommentForm()

    return render(request, 'detail.html', {
        'blog': blog,
        'comments': comments,
        'form': form,
        'is_liked': is_liked,
        'is_bookmarked': is_bookmarked
    })

@login_required
def like_blog(request, id):
    blog = get_object_or_404(Blog, id=id)
    if blog.likes.filter(id=request.user.id).exists():
        blog.likes.remove(request.user)
        liked = False
    else:
        blog.likes.add(request.user)
        liked = True
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'total_likes': blog.total_likes})
    return redirect('detail', id=id)

@login_required
def bookmark_blog(request, id):
    blog = get_object_or_404(Blog, id=id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, blog=blog)
    
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})
    return redirect('detail', id=id)

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    authored_blogs = user.authored_blogs.all().order_by('-created_at')
    bookmarked_blogs = Blog.objects.filter(bookmark__user=user)
    
    return render(request, 'profile.html', {
        'profile_user': user,
        'authored_blogs': authored_blogs,
        'bookmarked_blogs': bookmarked_blogs
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile_view', username=request.user.username)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')
    return render(request, 'register.html', {'form': form})

def user_login(request):
    form = AuthenticationForm(data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.is_staff:
            return redirect('admin_dashboard')
        return redirect('home')
    return render(request, 'login.html', {'form': form})

@staff_member_required
def admin_dashboard(request):
    blog_count = Blog.objects.count()
    category_count = Category.objects.count()
    comment_count = Comment.objects.count()
    user_count = User.objects.count()
    
    recent_blogs = Blog.objects.select_related('category').prefetch_related('authors').order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_comments = Comment.objects.order_by('-created_at')[:5]
    
    # Stats for Charts
    blogs_by_category = Blog.objects.values('category__name').annotate(count=Count('id'))
    
    context = {
        'blog_count': blog_count,
        'category_count': category_count,
        'comment_count': comment_count,
        'user_count': user_count,
        'recent_blogs': recent_blogs,
        'recent_users': recent_users,
        'recent_comments': recent_comments,
        'blogs_by_category': list(blogs_by_category)
    }
    return render(request, 'dashboard.html', context)

@staff_member_required
def blog_manage(request):
    blogs = Blog.objects.select_related('category').prefetch_related('authors').order_by('-created_at')
    return render(request, 'blog_manage.html', {'blogs': blogs})

@staff_member_required
def blog_add(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.save()
            form.save_m2m() # Important for authors ManyToMany
            if not blog.authors.exists():
                blog.authors.add(request.user)
            return redirect('blog_manage')
    else:
        form = BlogForm()
    return render(request, 'blog_form.html', {'form': form, 'title': 'Add Blog'})

@staff_member_required
def blog_edit(request, id):
    blog = get_object_or_404(Blog, id=id)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('blog_manage')
    else:
        form = BlogForm(instance=blog)
    return render(request, 'blog_form.html', {'form': form, 'title': 'Edit Blog'})

@staff_member_required
def blog_delete(request, id):
    blog = get_object_or_404(Blog, id=id)
    if request.method == 'POST':
        blog.delete()
        return redirect('blog_manage')
    return render(request, 'blog_confirm_delete.html', {'blog': blog})

def search_api(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    blogs = Blog.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).select_related('category').prefetch_related('authors')[:5]
    
    results = []
    for blog in blogs:
        results.append({
            'id': blog.id,
            'title': blog.title,
            'category': blog.category.name,
            'url': f'/blog/{blog.id}/',
            'image': blog.image.url if blog.image else None
        })
    
    return JsonResponse({'results': results})

def user_logout(request):
    logout(request)
    return redirect('home')
