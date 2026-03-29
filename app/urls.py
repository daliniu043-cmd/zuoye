from django.urls import path
from app import views

urlpatterns = [
    # 用户认证
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logOut/', views.logOut, name='logOut'),

    # 主页和用户管理
    path('home/', views.home, name='home'),
    path('changeSelfInfo/', views.changeSelfInfo, name='changeSelfInfo'),
    path('changePassword/', views.changePassword, name='changePassword'),

    # 【置顶】销售数据分析页面
    path('sales-analysis/', views.sales_analysis, name='sales_analysis'),

    # 游戏数据页面
    path('game-data/', views.game_data, name='game_data'),
    path('comment-data/', views.comment_data, name='comment_data'),
    path('game-favorites/', views.game_favorites, name='game_favorites'),
    path('game-recommendations/', views.game_recommendations, name='game_recommendations'),
    path('game-detail/<int:game_id>/', views.game_detail, name='game_detail'),

    # 可视化分析页面
    path('genre-analysis/', views.genre_analysis, name='genre_analysis'),
    path('publisher-analysis/', views.publisher_analysis, name='publisher_analysis'),
    path('platform-analysis/', views.platform_analysis, name='platform_analysis'),
    path('yearly-analysis/', views.yearly_analysis, name='yearly_analysis'),
    path('score-analysis/', views.score_analysis, name='score_analysis'),
    path('country-analysis/', views.country_analysis, name='country_analysis'),
    path('award-analysis/', views.award_analysis, name='award_analysis'),

    # 词云和情感分析
    path('word-cloud/', views.word_cloud, name='word_cloud'),
    path('sentiment-trend-analysis/', views.sentiment_trend_analysis, name='sentiment_trend_analysis'),

    # API接口
    path('api/chart-data/', views.api_chart_data, name='api_chart_data'),
    path('api/analyze-sentiment/', views.analyze_sentiment_api, name='analyze_sentiment_api'),
    path('api/analyze-sentiment-progress/<str:task_id>/', views.analyze_sentiment_progress_api, name='analyze_sentiment_progress_api'),
    path('api/sentiment-stats/', views.sentiment_stats_api, name='sentiment_stats_api'),
    path('api/test-sentiment/', views.test_sentiment_api, name='test_sentiment_api'),
    path('api/top-games-by-sales/', views.top_games_by_sales_api, name='top_games_by_sales_api'),
    path('api/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('api/submit-comment/', views.submit_comment, name='submit_comment'),
]
