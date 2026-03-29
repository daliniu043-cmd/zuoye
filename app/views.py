from django.shortcuts import render, redirect
from app.models import User, Game, Comment, GameFavorite
from django.http import HttpResponse, JsonResponse
from app.utils import errorResponse, getChangeSelfInfoData
from app.game_data_analysis import GameSalesDataAnalysis
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Avg, Count, Q, Sum, Max
import json, os, uuid, threading, time
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.conf import settings
from app.sentiment_analysis import analyze_comment_sentiment

sentiment_analysis_tasks = {}


def auto_analyze_sentiments():
    try:
        comments = Comment.objects.filter(sentiment='unknown')[:50]
        for comment in comments:
            if comment.content and len(comment.content.strip()) > 0:
                sentiment, score, confidence = analyze_comment_sentiment(comment.content)
                comment.sentiment = sentiment
                comment.sentiment_score = score
                comment.save()
    except:
        pass


# ==================== 用户认证 ====================

def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            User.objects.get(username=username, password=password)
            request.session['username'] = username
            return redirect('/app/home')
        except:
            return errorResponse.errorResponse(request, '用户名或密码错误')


def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')
        if not username or not password or not confirmPassword:
            return errorResponse.errorResponse(request, '不允许为空值')
        if password != confirmPassword:
            return errorResponse.errorResponse(request, '两次密码不一致')
        try:
            User.objects.get(username=username)
            return errorResponse.errorResponse(request, '该账号已存在')
        except User.DoesNotExist:
            User.objects.create(username=username, password=password)
            return redirect('/app/login')
    return errorResponse.errorResponse(request, '该账号已存在')


def logOut(request):
    request.session.flush()
    return redirect('/app/login')


# ==================== 首页 ====================

def home(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('login')

    analyzer = GameSalesDataAnalysis()
    basic_stats = analyzer.get_basic_statistics()

    # 销量Top10游戏
    top_games = list(Game.objects.order_by('-global_sales')[:10].values(
        'id', 'name', 'publisher', 'global_sales', 'genre', 'platform',
        'score', 'release_year', 'na_sales', 'eu_sales', 'jp_sales'
    ))

    # 最新添加的游戏
    recent_games = list(Game.objects.order_by('-create_time')[:10].values(
        'id', 'name', 'publisher', 'global_sales', 'genre', 'platform',
        'score', 'create_time'
    ))

    # 类型统计Top10
    genre_stats = list(Game.objects.exclude(genre='').values('genre').annotate(
        count=Count('id')
    ).order_by('-count')[:10])

    return render(request, 'home.html', {
        'userInfo': userInfo,
        'basic_stats': basic_stats,
        'top_games': top_games,
        'recent_games': recent_games,
        'top_categories': [(g['genre'], g['count']) for g in genre_stats],
        'active_menu': 'home'
    })


def changeSelfInfo(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    if request.method == 'POST':
        getChangeSelfInfoData.changeSelfInfo(username, request.POST, request.FILES)
        return redirect('/app/home')
    return render(request, 'changeSelfInfo.html', {'userInfo': userInfo, 'active_menu': 'changeSelfInfo'})


def changePassword(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    if request.method == 'POST':
        res = getChangeSelfInfoData.changePassword(userInfo, request.POST)
        if res is not None:
            return errorResponse.errorResponse(request, res)
        else:
            return redirect('/app/home')
    return render(request, 'changePassword.html', {'userInfo': userInfo, 'active_menu': 'changePassword'})


# ==================== 【置顶】销售数据分析 ====================

def sales_analysis(request):
    """游戏销售数据分析页面 - 核心页面"""
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('login')

    analyzer = GameSalesDataAnalysis()
    sales_data = analyzer.get_sales_analysis()

    return render(request, 'sales_analysis.html', {
        'userInfo': userInfo,
        'sales_data': json.dumps(sales_data, ensure_ascii=False, default=str),
        'active_menu': 'sales_analysis'
    })


# ==================== 游戏数据 ====================

def game_data(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)

    search_keyword = request.GET.get('search', '')
    search_type = request.GET.get('type', 'name')
    filter_genre = request.GET.get('genre', '')
    filter_platform = request.GET.get('platform', '')

    has_filters = search_keyword or filter_genre or filter_platform

    if has_filters:
        query = Q()
        if search_keyword:
            if search_type == 'name':
                query &= Q(name__icontains=search_keyword)
            elif search_type == 'publisher':
                query &= Q(publisher__icontains=search_keyword)
        if filter_genre:
            query &= Q(genre=filter_genre)
        if filter_platform:
            query &= Q(platform=filter_platform)
        games_data = list(Game.objects.filter(query).values(
            'id', 'name', 'publisher', 'genre', 'platform',
            'global_sales', 'score', 'release_year', 'global_rank',
            'na_sales', 'eu_sales', 'jp_sales', 'other_sales'
        ).order_by('-global_sales'))
    else:
        games_data = list(Game.objects.all().values(
            'id', 'name', 'publisher', 'genre', 'platform',
            'global_sales', 'score', 'release_year', 'global_rank',
            'na_sales', 'eu_sales', 'jp_sales', 'other_sales'
        ).order_by('-global_sales'))

    available_genres = sorted(list(Game.objects.exclude(genre='').values_list('genre', flat=True).distinct()))
    available_platforms = sorted(list(Game.objects.exclude(platform='').values_list('platform', flat=True).distinct()))

    paginator = Paginator(games_data, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    user_favorites = set(GameFavorite.objects.filter(user=userInfo).values_list('game_id', flat=True))
    for game in page_obj:
        game['is_favorited'] = game['id'] in user_favorites

    return render(request, 'game_data.html', {
        'userInfo': userInfo, 'page_obj': page_obj,
        'search_keyword': search_keyword, 'search_type': search_type,
        'filter_genre': filter_genre, 'filter_platform': filter_platform,
        'available_genres': available_genres, 'available_platforms': available_platforms,
        'active_menu': 'game_data'
    })


def comment_data(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('login')

    search_keyword = request.GET.get('search', '')
    search_type = request.GET.get('type', 'content')
    auto_analyze_sentiments()

    comments_query = Comment.objects.select_related('game').all()
    if search_keyword:
        if search_type == 'content':
            comments_query = comments_query.filter(content__icontains=search_keyword)
        elif search_type == 'user_name':
            comments_query = comments_query.filter(user_name__icontains=search_keyword)
        elif search_type == 'game_name':
            comments_query = comments_query.filter(game__name__icontains=search_keyword)
        elif search_type == 'sentiment':
            kw = search_keyword.lower()
            if kw in ['积极', 'positive', '正面', '好']:
                comments_query = comments_query.filter(sentiment='positive')
            elif kw in ['消极', 'negative', '负面', '差']:
                comments_query = comments_query.filter(sentiment='negative')
            elif kw in ['中性', 'neutral']:
                comments_query = comments_query.filter(sentiment='neutral')

    comments_query = comments_query.order_by('-create_time')
    paginator = Paginator(comments_query, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'comment_data.html', {
        'userInfo': userInfo, 'page_obj': page_obj,
        'search_keyword': search_keyword, 'search_type': search_type,
        'active_menu': 'comment_data'
    })


# ==================== 分析页面 ====================

def genre_analysis(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    data = analyzer.get_genre_analysis()
    return render(request, 'genre_analysis.html', {
        'userInfo': userInfo, 'category_data': json.dumps(data, default=str),
        'active_menu': 'genre_analysis'
    })


def publisher_analysis(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    return render(request, 'publisher_analysis.html', {
        'userInfo': userInfo, 'active_menu': 'publisher_analysis'
    })


def score_analysis(request):
    """评分分析页面"""
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    score_data = analyzer.get_score_analysis()
    return render(request, 'score_analysis.html', {
        'userInfo': userInfo,
        'score_data': json.dumps(score_data, ensure_ascii=False, default=str),
        'active_menu': 'score_analysis'
    })


def platform_analysis(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    data = analyzer.get_platform_analysis()
    return render(request, 'platform_analysis.html', {
        'userInfo': userInfo,
        'platform_data': json.dumps(data, ensure_ascii=False, default=str),
        'active_menu': 'platform_analysis'
    })


def yearly_analysis(request):
    """发行年份分析页面"""
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    yearly_data = analyzer.get_yearly_analysis()
    return render(request, 'yearly_analysis.html', {
        'userInfo': userInfo,
        'yearly_data': json.dumps(yearly_data, ensure_ascii=False, default=str),
        'active_menu': 'yearly_analysis'
    })


def country_analysis(request):
    """发行商国家分析页面"""
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    country_data = analyzer.get_country_analysis()
    return render(request, 'country_analysis.html', {
        'userInfo': userInfo,
        'country_data': json.dumps(country_data, ensure_ascii=False, default=str),
        'active_menu': 'country_analysis'
    })


def award_analysis(request):
    """获奖分析页面"""
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    analyzer = GameSalesDataAnalysis()
    award_data = analyzer.get_award_analysis()
    return render(request, 'award_analysis.html', {
        'userInfo': userInfo,
        'award_data': json.dumps(award_data, ensure_ascii=False, default=str),
        'active_menu': 'award_analysis'
    })


def word_cloud(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    userInfo = User.objects.get(username=username)
    text_type = request.GET.get('type', 'name')
    analyzer = GameSalesDataAnalysis()
    word_data = analyzer.generate_word_cloud_data(text_type)
    return render(request, 'word_cloud.html', {
        'userInfo': userInfo, 'word_data': json.dumps(word_data, ensure_ascii=False),
        'text_type': text_type, 'active_menu': 'word_cloud'
    })


def sentiment_trend_analysis(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('login')
    try:
        analyzer = GameSalesDataAnalysis()
        sentiment_data = analyzer.get_sentiment_trend_analysis()
        app_list = sentiment_data.get('app_sentiment_list', [])
        top_positive = app_list[:5]
        negative_apps = [a for a in app_list if a.get('avg_sentiment_score', 0) < 0]
        top_controversial = negative_apps[:5]
        sentiment_stats_dict = sentiment_data.get('sentiment_stats', {})
        return render(request, 'sentiment_trend_analysis.html', {
            'userInfo': userInfo,
            'sentiment_stats': sentiment_stats_dict,
            'sentiment_stats_json': json.dumps(sentiment_stats_dict, ensure_ascii=False),
            'genre_chart_data': json.dumps(sentiment_data.get('genre_chart_data', {'genres':[],'positive_rates':[],'negative_rates':[]}), ensure_ascii=False),
            'genre_sentiment_list': sentiment_data.get('genre_sentiment_list', []),
            'app_sentiment_list': app_list,
            'top_positive_apps': top_positive,
            'top_controversial_apps': top_controversial,
            'total_analyzed_comments': sentiment_data.get('total_analyzed_comments', 0),
            'active_menu': 'sentiment_trend_analysis'
        })
    except Exception as e:
        print(f"情感趋势分析错误: {e}")
        return render(request, 'sentiment_trend_analysis.html', {
            'userInfo': userInfo,
            'sentiment_stats': {}, 'sentiment_stats_json': '{}',
            'genre_chart_data': json.dumps({'genres':[],'positive_rates':[],'negative_rates':[]}),
            'genre_sentiment_list': [], 'app_sentiment_list': [],
            'top_positive_apps': [], 'top_controversial_apps': [],
            'total_analyzed_comments': 0, 'active_menu': 'sentiment_trend_analysis'
        })


# ==================== 游戏详情 ====================

def game_detail(request, game_id):
    try:
        username = request.session.get('username')
        userInfo = User.objects.get(username=username)
        game = Game.objects.get(id=game_id)
        comments = Comment.objects.filter(game=game).order_by('-create_time')[:50]
        comment_count = Comment.objects.filter(game=game).count()
        is_favorited = GameFavorite.objects.filter(user=userInfo, game=game).exists()

        from app.game_recommendation import get_recommendation_system
        rec_sys = get_recommendation_system(force_refresh=False)
        similar_games = rec_sys.get_similar_games(game_id, top_n=6)

        return render(request, 'game_detail.html', {
            'userInfo': userInfo, 'game': game, 'comments': comments,
            'comment_count': comment_count, 'is_favorited': is_favorited,
            'similar_games': similar_games,
        })
    except Game.DoesNotExist:
        return errorResponse.errorResponse(request, '游戏不存在')
    except User.DoesNotExist:
        return redirect('/app/login')
    except Exception as e:
        return errorResponse.errorResponse(request, f'获取游戏详情失败: {str(e)}')


def game_favorites(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
        favorites = GameFavorite.objects.filter(user=userInfo).select_related('game').order_by('-created_time')
        paginator = Paginator(favorites, 12)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'game_favorites.html', {
            'userInfo': userInfo, 'page_obj': page_obj,
            'favorites_count': favorites.count(), 'active_menu': 'game_favorites'
        })
    except User.DoesNotExist:
        return redirect('login')


def game_recommendations(request):
    username = request.session.get('username')
    if not username:
        return redirect('login')
    try:
        userInfo = User.objects.get(username=username)
        from app.game_recommendation import get_recommendation_system
        rec_sys = get_recommendation_system(force_refresh=True)
        recommendations = rec_sys.get_recommendations_for_user(userInfo.username)
        favorite_stats = rec_sys.get_user_favorite_stats(userInfo.username)
        return render(request, 'game_recommendations.html', {
            'userInfo': userInfo, 'recommendations': recommendations,
            'favorite_stats': favorite_stats, 'active_menu': 'game_recommendations'
        })
    except Exception as e:
        return render(request, 'game_recommendations.html', {
            'userInfo': userInfo, 'recommendations': [],
            'error_message': f'获取推荐失败: {str(e)}', 'active_menu': 'game_recommendations'
        })


# ==================== API接口 ====================

@require_http_methods(["POST"])
def toggle_favorite(request):
    try:
        username = request.session.get('username')
        if not username:
            return JsonResponse({'success': False, 'message': '用户未登录'})
        user = User.objects.get(username=username)
        data = json.loads(request.body)
        game_id = data.get('app_id') or data.get('game_id')
        if not game_id:
            return JsonResponse({'success': False, 'message': '游戏ID不能为空'})
        game = Game.objects.get(id=game_id)
        favorite, created = GameFavorite.objects.get_or_create(user=user, game=game)
        if created:
            return JsonResponse({'success': True, 'favorited': True, 'message': f'已收藏《{game.name}》'})
        else:
            favorite.delete()
            return JsonResponse({'success': True, 'favorited': False, 'message': f'已取消收藏《{game.name}》'})
    except Game.DoesNotExist:
        return JsonResponse({'success': False, 'message': '游戏不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'操作失败: {str(e)}'})


@require_http_methods(["POST"])
def submit_comment(request):
    try:
        username = request.session.get('username')
        if not username:
            return JsonResponse({'success': False, 'message': '用户未登录'})
        user = User.objects.get(username=username)
        data = json.loads(request.body)
        game_id = data.get('app_id') or data.get('game_id')
        content = data.get('content', '').strip()
        rating = data.get('rating', 0)
        if not game_id or not content:
            return JsonResponse({'success': False, 'message': '参数不完整'})
        if not (1 <= rating <= 5):
            return JsonResponse({'success': False, 'message': '评分必须在1-5之间'})
        game = Game.objects.get(id=game_id)
        comment = Comment.objects.create(
            game=game, user=user, user_name=user.username,
            content=content, rating=rating,
            comment_timestamp=int(datetime.now().timestamp())
        )
        try:
            sentiment, score, confidence = analyze_comment_sentiment(content)
            comment.sentiment = sentiment
            comment.sentiment_score = score
            comment.save()
        except:
            pass
        return JsonResponse({
            'success': True, 'message': '评论提交成功',
            'comment': {'id': comment.id, 'content': comment.content, 'rating': comment.rating,
                        'user_name': comment.user_name, 'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S')}
        })
    except Game.DoesNotExist:
        return JsonResponse({'success': False, 'message': '游戏不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'提交失败: {str(e)}'})


def top_games_by_sales_api(request):
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 10))
        top_games = Game.objects.order_by('-global_sales')[:limit]
        data = [{'rank': i, 'id': g.id, 'name': g.name, 'publisher': g.publisher,
                 'global_sales': g.global_sales, 'genre': g.genre, 'platform': g.platform,
                 'score': g.score} for i, g in enumerate(top_games, 1)]
        return JsonResponse({'success': True, 'data': data})
    return JsonResponse({'success': False, 'message': '无效请求'})


def api_chart_data(request):
    chart_type = request.GET.get('type', '')
    analyzer = GameSalesDataAnalysis()
    if chart_type == 'category' or chart_type == 'genre':
        data = analyzer.get_genre_analysis()
    elif chart_type == 'publisher' or chart_type == 'developer_publisher':
        data = analyzer.get_publisher_analysis()
    elif chart_type == 'rating':
        data = analyzer.get_score_analysis()
    elif chart_type == 'sentiment':
        data = analyzer.get_sentiment_trend_analysis()
    elif chart_type == 'platform':
        data = analyzer.get_platform_analysis()
    elif chart_type == 'release_date' or chart_type == 'release_year':
        data = analyzer.get_yearly_analysis()
    elif chart_type == 'sales':
        data = analyzer.get_sales_analysis()
    else:
        data = {'error': '未知的图表类型'}
    return JsonResponse(data, safe=False)


def analyze_sentiment_batch(task_id, batch_size=100, force_reanalyze=False):
    try:
        if force_reanalyze:
            comments = list(Comment.objects.all().select_related('game'))
        else:
            comments = list(Comment.objects.filter(sentiment='unknown').select_related('game'))
        total_count = len(comments)
        processed_count = 0
        success_count = 0
        sentiment_analysis_tasks[task_id] = {
            'total': total_count, 'processed': 0, 'success': 0,
            'status': '正在准备分析...', 'completed': False, 'start_time': datetime.now()
        }
        if total_count == 0:
            sentiment_analysis_tasks[task_id].update({'status': '没有需要分析的评论', 'completed': True})
            return
        for comment in comments:
            if comment.content and len(comment.content.strip()) > 0:
                try:
                    sentiment, score, confidence = analyze_comment_sentiment(comment.content)
                    comment.sentiment = sentiment
                    comment.sentiment_score = score
                    comment.save()
                    success_count += 1
                except:
                    pass
            processed_count += 1
            if processed_count % 10 == 0 or processed_count == total_count:
                pct = round((processed_count / total_count) * 100, 1)
                sentiment_analysis_tasks[task_id].update({
                    'processed': processed_count, 'success': success_count,
                    'status': f'已分析 {processed_count}/{total_count} ({pct}%)'
                })
        sentiment_analysis_tasks[task_id].update({
            'processed': processed_count, 'success': success_count,
            'status': f'完成！处理 {processed_count} 条，成功 {success_count} 条',
            'completed': True, 'end_time': datetime.now()
        })
    except Exception as e:
        if task_id not in sentiment_analysis_tasks:
            sentiment_analysis_tasks[task_id] = {'total': 0, 'processed': 0, 'success': 0, 'completed': True}
        sentiment_analysis_tasks[task_id].update({'status': f'失败: {str(e)}', 'completed': True})


def analyze_sentiment_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = str(uuid.uuid4())
            thread = threading.Thread(target=analyze_sentiment_batch, args=(task_id, data.get('batch_size', 100), data.get('force_reanalyze', False)))
            thread.daemon = True
            thread.start()
            return JsonResponse({'success': True, 'task_id': task_id, 'message': '情感分析任务已启动'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': '无效请求'})


def analyze_sentiment_progress_api(request, task_id):
    if task_id in sentiment_analysis_tasks:
        return JsonResponse({'success': True, 'progress': sentiment_analysis_tasks[task_id]})
    return JsonResponse({'success': False, 'message': '任务不存在'})


def sentiment_stats_api(request):
    total = Comment.objects.count()
    pos = Comment.objects.filter(sentiment='positive').count()
    neg = Comment.objects.filter(sentiment='negative').count()
    neu = Comment.objects.filter(sentiment='neutral').count()
    unk = Comment.objects.filter(sentiment='unknown').count()
    pct = lambda c: round(c/total*100, 1) if total > 0 else 0
    return JsonResponse({'success': True, 'stats': {
        'total': total, 'positive': pos, 'negative': neg, 'neutral': neu, 'unknown': unk,
        'positive_percentage': pct(pos), 'negative_percentage': pct(neg),
        'neutral_percentage': pct(neu), 'unknown_percentage': pct(unk),
    }})


def test_sentiment_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        if not text.strip():
            return JsonResponse({'success': False, 'message': '请输入文本'})
        sentiment, score, confidence = analyze_comment_sentiment(text)
        return JsonResponse({'success': True, 'result': {
            'text': text, 'sentiment': sentiment, 'score': round(score, 3), 'confidence': round(confidence, 3),
            'sentiment_display': {'positive':'积极 😊','negative':'消极 😔','neutral':'中性 😐','unknown':'未知 ❓'}.get(sentiment, '未知')
        }})
    return JsonResponse({'success': True, 'test_cases': [
        "这款游戏太棒了，好评！", "太无聊了，浪费时间", "还行吧，一般般"
    ]})
