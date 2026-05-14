
from django.contrib import admin
from .models import Blog, Category, Comment
from django.db.models import Count

class BlogAdminSite(admin.AdminSite):
    site_header = "Blog System Dashboard"
    site_title = "Admin Portal"
    index_title = "Welcome to the Blog Management System"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['blog_count'] = Blog.objects.count()
        extra_context['category_count'] = Category.objects.count()
        extra_context['comment_count'] = Comment.objects.count()
        extra_context['recent_blogs'] = Blog.objects.order_by('-created_at')[:5]
        return super().index(request, extra_context)

admin_site = BlogAdminSite(name='myadmin')

@admin.register(Blog, site=admin_site)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_authors', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content')
    list_per_page = 20

    def get_authors(self, obj):
        return ", ".join([a.username for a in obj.authors.all()])
    get_authors.short_description = 'Authors'

@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'blog_count')
    
    def blog_count(self, obj):
        return obj.blog_set.count()
    blog_count.short_description = 'Number of Blogs'

@admin.register(Comment, site=admin_site)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'blog', 'created_at', 'text_snippet')
    list_filter = ('created_at',)
    
    def text_snippet(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_snippet.short_description = 'Comment'
