
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/<int:id>/', views.detail, name='detail'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # New Features
    path('blog/<int:id>/like/', views.like_blog, name='like_blog'),
    path('blog/<int:id>/bookmark/', views.bookmark_blog, name='bookmark_blog'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    
    # Admin Dashboard Routes
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/blogs/', views.blog_manage, name='blog_manage'),
    path('dashboard/blogs/add/', views.blog_add, name='blog_add'),
    path('dashboard/blogs/edit/<int:id>/', views.blog_edit, name='blog_edit'),
    path('dashboard/blogs/delete/<int:id>/', views.blog_delete, name='blog_delete'),
    
    # API Routes
    path('api/search/', views.search_api, name='search_api'),
]
