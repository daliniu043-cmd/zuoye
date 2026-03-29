from django.contrib import admin
from app.models import User, Game, Comment, GameFavorite
from django.utils.html import format_html

admin.site.site_header = "游戏销售数据可视化分析管理系统"
admin.site.site_title = "游戏销售管理"
admin.site.index_title = "欢迎使用游戏销售数据可视化分析管理系统"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'sex', 'address', 'textarea', 'createTime']
    list_per_page = 20
    ordering = ('id',)
    list_display_links = ['id', 'username']
    search_fields = ['username', 'address']
    list_filter = ['sex', 'createTime']
    readonly_fields = ['id', 'createTime']
    fieldsets = (
        ('基本信息', {'fields': ('id', 'username', 'password')}),
        ('个人资料', {'fields': ('sex', 'address', 'textarea', 'avatar')}),
        ('时间信息', {'fields': ('createTime',), 'classes': ('collapse',)}),
    )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['id', 'global_rank', 'name', 'platform', 'genre', 'publisher',
                    'global_sales', 'score', 'release_year']
    list_per_page = 25
    ordering = ('global_rank',)
    list_display_links = ['id', 'name']
    search_fields = ['name', 'publisher', 'genre', 'platform']
    list_filter = ['genre', 'platform', 'publisher', 'media_review', 'player_review', 'is_awarded']
    readonly_fields = ['id', 'create_time', 'update_time']
    fieldsets = (
        ('基本信息', {'fields': ('id', 'global_rank', 'name', 'platform', 'release_year')}),
        ('分类信息', {'fields': ('genre', 'publisher', 'publisher_country')}),
        ('销售数据', {'fields': ('na_sales', 'eu_sales', 'jp_sales', 'other_sales', 'global_sales')}),
        ('评价信息', {'fields': ('score', 'avg_playtime', 'media_review', 'player_review')}),
        ('其他信息', {'fields': ('multiplayer', 'has_dlc', 'is_awarded', 'award_count', 'language_count')}),
        ('时间信息', {'fields': ('create_time', 'update_time'), 'classes': ('collapse',)}),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'game_name', 'user_name', 'rating', 'sentiment', 'sentiment_score', 'comment_time']
    list_per_page = 30
    ordering = ('-id',)
    list_display_links = ['id', 'user_name']
    search_fields = ['user_name', 'content', 'game__name']
    list_filter = ['sentiment', 'rating']
    readonly_fields = ['id', 'create_time']

    def game_name(self, obj):
        return obj.game.name if obj.game else "未知"
    game_name.short_description = "游戏名称"

    fieldsets = (
        ('基本信息', {'fields': ('id', 'game', 'user', 'user_name')}),
        ('评论内容', {'fields': ('content', 'rating', 'like_count', 'reply_count', 'comment_time')}),
        ('情感分析', {'fields': ('sentiment', 'sentiment_score'), 'classes': ('collapse',)}),
        ('时间信息', {'fields': ('create_time',), 'classes': ('collapse',)}),
    )


@admin.register(GameFavorite)
class GameFavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_display', 'game_display', 'notes', 'created_time']
    list_per_page = 30
    ordering = ('-created_time',)
    search_fields = ['user__username', 'game__name']

    def user_display(self, obj):
        return obj.user.username if obj.user else "未知"
    user_display.short_description = "用户"

    def game_display(self, obj):
        return obj.game.name if obj.game else "未知"
    game_display.short_description = "游戏"
