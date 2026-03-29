#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏销售数据分析模块
====================================
提供各种游戏销售数据分析和统计功能，包括：
- 基础统计数据
- 销售数据综合分析（核心页面）
- 游戏类型分析
- 平台分析
- 发行商分析
- 发行年份分析
- 评分分析
- 发行商国家分析
- 获奖分析
- 词云数据生成
- 情感趋势分析
"""

from collections import defaultdict, Counter
import re
from django.db.models import Avg, Count, Sum, Max, Min, Q, F
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

from app.models import Game, Comment, GameFavorite


class GameSalesDataAnalysis:
    """
    游戏销售数据分析类
    提供全面的游戏销售数据分析功能，
    包括地区销量分析、平台分析、类型分析、发行商分析等。
    """

    def __init__(self):
        """初始化分析实例"""
        self.games = Game.objects.all()
        self.comments = Comment.objects.all()

    # ============================================================
    # 基础统计数据
    # ============================================================
    def get_basic_statistics(self):
        """获取系统基础统计数据概览"""
        try:
            total_games = self.games.count()
            total_comments = self.comments.count()
            agg = self.games.aggregate(
                total_global_sales=Sum('global_sales'),
                avg_global_sales=Avg('global_sales'),
                max_global_sales=Max('global_sales'),
                min_global_sales=Min('global_sales'),
                avg_score=Avg('score'), max_score=Max('score'),
                total_na=Sum('na_sales'), total_eu=Sum('eu_sales'),
                total_jp=Sum('jp_sales'), total_other=Sum('other_sales'),
                avg_playtime=Avg('avg_playtime'),
                avg_language_count=Avg('language_count'),
            )
            total_publishers = self.games.exclude(publisher='').values('publisher').distinct().count()
            total_platforms = self.games.exclude(platform='').values('platform').distinct().count()
            total_genres = self.games.exclude(genre='').values('genre').distinct().count()
            awarded_games = self.games.filter(is_awarded=True).count()
            multiplayer_games = self.games.filter(multiplayer=True).count()
            dlc_games = self.games.filter(has_dlc=True).count()
            positive_media = self.games.filter(media_review='好评').count()
            negative_media = self.games.filter(media_review='差评').count()
            return {
                'total_games': total_games, 'total_comments': total_comments,
                'total_global_sales': round(agg['total_global_sales'] or 0, 2),
                'avg_global_sales': round(agg['avg_global_sales'] or 0, 4),
                'max_global_sales': round(agg['max_global_sales'] or 0, 2),
                'min_global_sales': round(agg['min_global_sales'] or 0, 2),
                'avg_score': round(agg['avg_score'] or 0, 2),
                'max_score': round(agg['max_score'] or 0, 1),
                'total_na_sales': round(agg['total_na'] or 0, 2),
                'total_eu_sales': round(agg['total_eu'] or 0, 2),
                'total_jp_sales': round(agg['total_jp'] or 0, 2),
                'total_other_sales': round(agg['total_other'] or 0, 2),
                'avg_playtime': round(agg['avg_playtime'] or 0, 1),
                'avg_language_count': round(agg['avg_language_count'] or 0, 1),
                'total_publishers': total_publishers, 'total_platforms': total_platforms,
                'total_genres': total_genres, 'awarded_games': awarded_games,
                'multiplayer_games': multiplayer_games, 'dlc_games': dlc_games,
                'positive_media': positive_media, 'negative_media': negative_media,
            }
        except Exception as e:
            print(f"获取基础统计数据失败: {e}")
            import traceback; traceback.print_exc()
            return {k: 0 for k in ['total_games','total_comments','total_global_sales','avg_global_sales','max_global_sales','min_global_sales','avg_score','max_score','total_na_sales','total_eu_sales','total_jp_sales','total_other_sales','avg_playtime','avg_language_count','total_publishers','total_platforms','total_genres','awarded_games','multiplayer_games','dlc_games','positive_media','negative_media']}

    # ============================================================
    # 销售数据综合分析（核心页面）
    # ============================================================
    def get_sales_analysis(self):
        """获取销售数据综合分析（用于销售分析核心页面）"""
        try:
            # 1. 各地区销量对比
            region_sales = self.games.aggregate(na=Sum('na_sales'),eu=Sum('eu_sales'),jp=Sum('jp_sales'),other=Sum('other_sales'),total=Sum('global_sales'))
            region_data = {
                'labels': ['北美地区', '欧洲地区', '日本地区', '其他地区'],
                'values': [round(region_sales['na'] or 0,2), round(region_sales['eu'] or 0,2), round(region_sales['jp'] or 0,2), round(region_sales['other'] or 0,2)],
                'total': round(region_sales['total'] or 0, 2)
            }
            # 2. 年度销量趋势
            yearly_qs = self.games.filter(year__gte=1980,year__lte=2025).values('year').annotate(
                total_sales=Sum('global_sales'),game_count=Count('id'),avg_score=Avg('score'),
                na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),
                awarded_count=Count('id',filter=Q(is_awarded=True)),
            ).order_by('year')
            yearly_trend = {
                'years': [y['year'] for y in yearly_qs],
                'sales': [round(y['total_sales'] or 0,2) for y in yearly_qs],
                'counts': [y['game_count'] for y in yearly_qs],
                'avg_scores': [round(y['avg_score'] or 0,2) for y in yearly_qs],
                'na_sales': [round(y['na_sales'] or 0,2) for y in yearly_qs],
                'eu_sales': [round(y['eu_sales'] or 0,2) for y in yearly_qs],
                'jp_sales': [round(y['jp_sales'] or 0,2) for y in yearly_qs],
                'awarded_counts': [y['awarded_count'] for y in yearly_qs],
            }
            # 3. 平台销量TOP15
            plat_qs = self.games.values('platform').annotate(total_sales=Sum('global_sales'),game_count=Count('id'),avg_score=Avg('score'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales')).order_by('-total_sales')[:15]
            platform_data = {
                'platforms': [p['platform'] for p in plat_qs], 'sales': [round(p['total_sales'] or 0,2) for p in plat_qs],
                'counts': [p['game_count'] for p in plat_qs], 'avg_scores': [round(p['avg_score'] or 0,2) for p in plat_qs],
                'avg_sales': [round(p['avg_sales'] or 0,4) for p in plat_qs], 'max_sales': [round(p['max_sales'] or 0,2) for p in plat_qs],
            }
            # 4. 发行商销量TOP15
            pub_qs = self.games.exclude(publisher='').values('publisher').annotate(total_sales=Sum('global_sales'),game_count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),other_sales=Sum('other_sales'),awarded_count=Count('id',filter=Q(is_awarded=True)),multiplayer_count=Count('id',filter=Q(multiplayer=True))).order_by('-total_sales')[:15]
            publisher_data = {
                'publishers': [p['publisher'] for p in pub_qs], 'sales': [round(p['total_sales'] or 0,2) for p in pub_qs],
                'counts': [p['game_count'] for p in pub_qs], 'na_sales': [round(p['na_sales'] or 0,2) for p in pub_qs],
                'eu_sales': [round(p['eu_sales'] or 0,2) for p in pub_qs], 'jp_sales': [round(p['jp_sales'] or 0,2) for p in pub_qs],
                'avg_scores': [round(p['avg_score'] or 0,2) for p in pub_qs],
            }
            # 5. 游戏类型销量
            genre_qs = self.games.exclude(genre='').values('genre').annotate(total_sales=Sum('global_sales'),game_count=Count('id'),avg_score=Avg('score'),avg_sales=Avg('global_sales'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),other_sales=Sum('other_sales'),awarded_count=Count('id',filter=Q(is_awarded=True)),multiplayer_count=Count('id',filter=Q(multiplayer=True)),avg_playtime=Avg('avg_playtime')).order_by('-total_sales')
            genre_data = {
                'genres': [g['genre'] for g in genre_qs], 'sales': [round(g['total_sales'] or 0,2) for g in genre_qs],
                'counts': [g['game_count'] for g in genre_qs], 'avg_scores': [round(g['avg_score'] or 0,2) for g in genre_qs],
                'na_sales': [round(g['na_sales'] or 0,2) for g in genre_qs], 'eu_sales': [round(g['eu_sales'] or 0,2) for g in genre_qs],
                'jp_sales': [round(g['jp_sales'] or 0,2) for g in genre_qs],
            }
            # 6. TOP20畅销游戏
            top_games = list(self.games.order_by('global_rank')[:20].values('id','global_rank','name','platform','year','genre','publisher','publisher_country','global_sales','na_sales','eu_sales','jp_sales','other_sales','score','avg_playtime','media_review','player_review','is_awarded','award_count','multiplayer','has_dlc'))
            # 7. 媒体评价分布
            media_dist = list(self.games.exclude(media_review='').values('media_review').annotate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales')).order_by('-count'))
            # 8. 获奖对比
            aw = self.games.filter(is_awarded=True).aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'),max_sales=Max('global_sales'))
            naw = self.games.filter(is_awarded=False).aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'),max_sales=Max('global_sales'))
            awarded_stats = {
                'awarded': {k: round(v,2) if isinstance(v,float) else (v or 0) for k,v in aw.items()},
                'not_awarded': {k: round(v,2) if isinstance(v,float) else (v or 0) for k,v in naw.items()},
            }
            return {'region_data':region_data,'yearly_trend':yearly_trend,'platform_data':platform_data,'publisher_data':publisher_data,'genre_data':genre_data,'top_games':top_games,'media_dist':media_dist,'awarded_stats':awarded_stats}
        except Exception as e:
            print(f"获取销售分析数据失败: {e}"); import traceback; traceback.print_exc()
            return {}

    # ============================================================
    # 游戏类型分析
    # ============================================================
    def get_genre_analysis(self):
        """获取游戏类型分析数据"""
        try:
            genre_qs = self.games.exclude(genre='').exclude(genre__isnull=True).values('genre').annotate(
                count=Count('id'),total_sales=Sum('global_sales'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),
                avg_score=Avg('score'),max_score=Max('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),
                jp_sales=Sum('jp_sales'),other_sales=Sum('other_sales'),awarded_count=Count('id',filter=Q(is_awarded=True)),
                multiplayer_count=Count('id',filter=Q(multiplayer=True)),dlc_count=Count('id',filter=Q(has_dlc=True)),
                avg_playtime=Avg('avg_playtime'),avg_language=Avg('language_count'),
            ).order_by('-total_sales')
            genre_list = []
            for g in genre_qs:
                d = {
                    'genre': g['genre'], 'count': g['count'],
                    'total_sales': round(g['total_sales'] or 0,2), 'avg_sales': round(g['avg_sales'] or 0,4),
                    'max_sales': round(g['max_sales'] or 0,2), 'avg_score': round(g['avg_score'] or 0,2),
                    'max_score': round(g['max_score'] or 0,1),
                    'na_sales': round(g['na_sales'] or 0,2), 'eu_sales': round(g['eu_sales'] or 0,2),
                    'jp_sales': round(g['jp_sales'] or 0,2), 'other_sales': round(g['other_sales'] or 0,2),
                    'awarded_count': g['awarded_count'], 'multiplayer_count': g['multiplayer_count'],
                    'dlc_count': g['dlc_count'], 'avg_playtime': round(g['avg_playtime'] or 0,1),
                    'avg_language': round(g['avg_language'] or 0,1),
                    'awarded_ratio': round(g['awarded_count']/g['count']*100,1) if g['count']>0 else 0,
                    'multiplayer_ratio': round(g['multiplayer_count']/g['count']*100,1) if g['count']>0 else 0,
                }
                genre_list.append(d)
            return {'genres':[g['genre'] for g in genre_list],'counts':[g['count'] for g in genre_list],'total_sales':[g['total_sales'] for g in genre_list],'avg_sales':[g['avg_sales'] for g in genre_list],'avg_scores':[g['avg_score'] for g in genre_list],'na_sales':[g['na_sales'] for g in genre_list],'eu_sales':[g['eu_sales'] for g in genre_list],'jp_sales':[g['jp_sales'] for g in genre_list],'genre_list':genre_list}
        except Exception as e:
            print(f"获取游戏类型分析失败: {e}"); import traceback; traceback.print_exc()
            return {'genres':[],'counts':[],'total_sales':[],'avg_sales':[],'avg_scores':[],'na_sales':[],'eu_sales':[],'jp_sales':[],'genre_list':[]}

    # ============================================================
    # 平台分析
    # ============================================================
    def get_platform_analysis(self):
        """获取游戏平台分析数据"""
        try:
            plat_qs = self.games.exclude(platform='').exclude(platform__isnull=True).values('platform').annotate(
                count=Count('id'),total_sales=Sum('global_sales'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),
                avg_score=Avg('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),
                other_sales=Sum('other_sales'),min_year=Min('year',filter=Q(year__gt=0)),max_year=Max('year',filter=Q(year__gt=0)),
                awarded_count=Count('id',filter=Q(is_awarded=True)),multiplayer_count=Count('id',filter=Q(multiplayer=True)),
                avg_playtime=Avg('avg_playtime'),
            ).order_by('-total_sales')
            platform_list = []
            for p in plat_qs:
                d = {
                    'platform': p['platform'], 'count': p['count'],
                    'total_sales': round(p['total_sales'] or 0,2), 'avg_sales': round(p['avg_sales'] or 0,4),
                    'max_sales': round(p['max_sales'] or 0,2), 'avg_score': round(p['avg_score'] or 0,2),
                    'na_sales': round(p['na_sales'] or 0,2), 'eu_sales': round(p['eu_sales'] or 0,2),
                    'jp_sales': round(p['jp_sales'] or 0,2), 'other_sales': round(p['other_sales'] or 0,2),
                    'min_year': p['min_year'] or 0, 'max_year': p['max_year'] or 0,
                    'awarded_count': p['awarded_count'], 'multiplayer_count': p['multiplayer_count'],
                    'avg_playtime': round(p['avg_playtime'] or 0,1),
                    'na_ratio': round((p['na_sales'] or 0)/(p['total_sales'] or 1)*100,1),
                }
                platform_list.append(d)
            return {'platforms':[p['platform'] for p in platform_list],'counts':[p['count'] for p in platform_list],'total_sales':[p['total_sales'] for p in platform_list],'avg_scores':[p['avg_score'] for p in platform_list],'platform_list':platform_list}
        except Exception as e:
            print(f"获取平台分析失败: {e}"); import traceback; traceback.print_exc()
            return {'platforms':[],'counts':[],'total_sales':[],'avg_scores':[],'platform_list':[]}

    # ============================================================
    # 发行商分析
    # ============================================================
    def get_publisher_analysis(self):
        """获取发行商分析数据（TOP25）"""
        try:
            pub_qs = self.games.exclude(publisher='').exclude(publisher__isnull=True).values('publisher').annotate(
                game_count=Count('id'),total_sales=Sum('global_sales'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),
                avg_score=Avg('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),other_sales=Sum('other_sales'),
                awarded_count=Count('id',filter=Q(is_awarded=True)),multiplayer_count=Count('id',filter=Q(multiplayer=True)),
                dlc_count=Count('id',filter=Q(has_dlc=True)),avg_playtime=Avg('avg_playtime'),
                min_year=Min('year',filter=Q(year__gt=0)),max_year=Max('year',filter=Q(year__gt=0)),
            ).order_by('-total_sales')[:25]
            publisher_list = []
            for pub in pub_qs:
                top_games = list(self.games.filter(publisher=pub['publisher']).order_by('-global_sales')[:5].values('id','name','platform','global_sales','score','genre'))
                genre_counter = Counter()
                for g in self.games.filter(publisher=pub['publisher']).values_list('genre',flat=True):
                    if g: genre_counter[g] += 1
                main_genres = [g[0] for g in genre_counter.most_common(3)]
                platform_counter = Counter()
                for p in self.games.filter(publisher=pub['publisher']).values_list('platform',flat=True):
                    if p: platform_counter[p] += 1
                main_platforms = [p[0] for p in platform_counter.most_common(3)]
                d = {
                    'publisher': pub['publisher'], 'game_count': pub['game_count'],
                    'total_sales': round(pub['total_sales'] or 0,2), 'avg_sales': round(pub['avg_sales'] or 0,4),
                    'max_sales': round(pub['max_sales'] or 0,2), 'avg_score': round(pub['avg_score'] or 0,2),
                    'na_sales': round(pub['na_sales'] or 0,2), 'eu_sales': round(pub['eu_sales'] or 0,2),
                    'jp_sales': round(pub['jp_sales'] or 0,2), 'other_sales': round(pub['other_sales'] or 0,2),
                    'awarded_count': pub['awarded_count'], 'multiplayer_count': pub['multiplayer_count'],
                    'dlc_count': pub['dlc_count'], 'avg_playtime': round(pub['avg_playtime'] or 0,1),
                    'active_years': f"{pub['min_year'] or '?'}-{pub['max_year'] or '?'}",
                    'top_games': top_games, 'main_genres': main_genres, 'main_platforms': main_platforms,
                    'awarded_ratio': round(pub['awarded_count']/pub['game_count']*100,1) if pub['game_count']>0 else 0,
                }
                publisher_list.append(d)
            return {'publishers':[p['publisher'] for p in publisher_list],'game_counts':[p['game_count'] for p in publisher_list],'total_sales':[p['total_sales'] for p in publisher_list],'avg_scores':[p['avg_score'] for p in publisher_list],'na_sales':[p['na_sales'] for p in publisher_list],'eu_sales':[p['eu_sales'] for p in publisher_list],'jp_sales':[p['jp_sales'] for p in publisher_list],'publisher_list':publisher_list}
        except Exception as e:
            print(f"获取发行商分析失败: {e}"); import traceback; traceback.print_exc()
            return {'publishers':[],'game_counts':[],'total_sales':[],'avg_scores':[],'na_sales':[],'eu_sales':[],'jp_sales':[],'publisher_list':[]}

    # ============================================================
    # 发行年份分析
    # ============================================================
    def get_yearly_analysis(self):
        """获取发行年份趋势分析数据"""
        try:
            yearly_qs = self.games.filter(year__gte=1980,year__lte=2025).values('year').annotate(
                count=Count('id'),total_sales=Sum('global_sales'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),
                avg_score=Avg('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),
                other_sales=Sum('other_sales'),awarded_count=Count('id',filter=Q(is_awarded=True)),
                multiplayer_count=Count('id',filter=Q(multiplayer=True)),avg_playtime=Avg('avg_playtime'),
            ).order_by('year')
            yearly_list = []
            for y in yearly_qs:
                d = {
                    'year': y['year'], 'count': y['count'],
                    'total_sales': round(y['total_sales'] or 0,2), 'avg_sales': round(y['avg_sales'] or 0,4),
                    'max_sales': round(y['max_sales'] or 0,2), 'avg_score': round(y['avg_score'] or 0,2),
                    'na_sales': round(y['na_sales'] or 0,2), 'eu_sales': round(y['eu_sales'] or 0,2),
                    'jp_sales': round(y['jp_sales'] or 0,2), 'other_sales': round(y['other_sales'] or 0,2),
                    'awarded_count': y['awarded_count'], 'multiplayer_count': y['multiplayer_count'],
                    'avg_playtime': round(y['avg_playtime'] or 0,1),
                }
                yearly_list.append(d)
            return {'years':[y['year'] for y in yearly_list],'counts':[y['count'] for y in yearly_list],'total_sales':[y['total_sales'] for y in yearly_list],'avg_sales':[y['avg_sales'] for y in yearly_list],'avg_scores':[y['avg_score'] for y in yearly_list],'na_sales':[y['na_sales'] for y in yearly_list],'eu_sales':[y['eu_sales'] for y in yearly_list],'jp_sales':[y['jp_sales'] for y in yearly_list],'yearly_list':yearly_list}
        except Exception as e:
            print(f"获取年份分析失败: {e}"); import traceback; traceback.print_exc()
            return {'years':[],'counts':[],'total_sales':[],'avg_sales':[],'avg_scores':[],'na_sales':[],'eu_sales':[],'jp_sales':[],'yearly_list':[]}

    # ============================================================
    # 评分分析
    # ============================================================
    def get_score_analysis(self):
        """获取游戏评分分析数据"""
        try:
            score_ranges = {
                '9-10分 (神作)': self.games.filter(score__gte=9.0).count(),
                '8-9分 (优秀)': self.games.filter(score__gte=8.0,score__lt=9.0).count(),
                '7-8分 (良好)': self.games.filter(score__gte=7.0,score__lt=8.0).count(),
                '6-7分 (中等)': self.games.filter(score__gte=6.0,score__lt=7.0).count(),
                '5-6分 (一般)': self.games.filter(score__gte=5.0,score__lt=6.0).count(),
                '5分以下 (较差)': self.games.filter(score__gt=0,score__lt=5.0).count(),
                '未评分': self.games.filter(score=0).count(),
            }
            score_sales_data = []
            for s in range(0, 20):
                low, high = s*0.5, (s+1)*0.5
                seg = self.games.filter(score__gte=low,score__lt=high)
                cnt = seg.count()
                if cnt > 0:
                    avg_s = seg.aggregate(avg=Avg('global_sales'))['avg'] or 0
                    score_sales_data.append({'score_range':f"{low:.1f}-{high:.1f}",'avg_sales':round(avg_s,4),'count':cnt})
            media_vs_sales = list(self.games.exclude(media_review='').values('media_review').annotate(avg_sales=Avg('global_sales'),total_sales=Sum('global_sales'),count=Count('id'),avg_score=Avg('score'),max_sales=Max('global_sales'),awarded_ratio=Count('id',filter=Q(is_awarded=True))).order_by('-avg_sales'))
            player_vs_sales = list(self.games.exclude(player_review='').values('player_review').annotate(avg_sales=Avg('global_sales'),total_sales=Sum('global_sales'),count=Count('id'),avg_score=Avg('score'),max_sales=Max('global_sales')).order_by('-avg_sales'))
            high_score = self.games.filter(score__gte=8.0).aggregate(count=Count('id'),avg_sales=Avg('global_sales'),total_sales=Sum('global_sales'),avg_playtime=Avg('avg_playtime'),awarded_count=Count('id',filter=Q(is_awarded=True)),multiplayer_count=Count('id',filter=Q(multiplayer=True)))
            return {'score_ranges':score_ranges,'score_vs_sales':score_sales_data,'media_vs_sales':media_vs_sales,'player_vs_sales':player_vs_sales,'high_score_stats':{k:round(v,2) if isinstance(v,float) else v for k,v in (high_score or {}).items()}}
        except Exception as e:
            print(f"获取评分分析失败: {e}"); import traceback; traceback.print_exc()
            return {'score_ranges':{},'score_vs_sales':[],'media_vs_sales':[],'player_vs_sales':[],'high_score_stats':{}}

    # ============================================================
    # 发行商国家分析
    # ============================================================
    def get_country_analysis(self):
        """获取发行商国家分析数据"""
        try:
            country_qs = self.games.exclude(publisher_country='').exclude(publisher_country__isnull=True).values('publisher_country').annotate(
                game_count=Count('id'),total_sales=Sum('global_sales'),avg_sales=Avg('global_sales'),max_sales=Max('global_sales'),
                avg_score=Avg('score'),na_sales=Sum('na_sales'),eu_sales=Sum('eu_sales'),jp_sales=Sum('jp_sales'),
                other_sales=Sum('other_sales'),awarded_count=Count('id',filter=Q(is_awarded=True)),
                publisher_count=Count('publisher',distinct=True),avg_playtime=Avg('avg_playtime'),
            ).order_by('-total_sales')
            country_list = []
            for c in country_qs:
                d = {
                    'publisher_country': c['publisher_country'], 'game_count': c['game_count'],
                    'total_sales': round(c['total_sales'] or 0,2), 'avg_sales': round(c['avg_sales'] or 0,4),
                    'max_sales': round(c['max_sales'] or 0,2), 'avg_score': round(c['avg_score'] or 0,2),
                    'na_sales': round(c['na_sales'] or 0,2), 'eu_sales': round(c['eu_sales'] or 0,2),
                    'jp_sales': round(c['jp_sales'] or 0,2), 'other_sales': round(c['other_sales'] or 0,2),
                    'awarded_count': c['awarded_count'], 'publisher_count': c['publisher_count'],
                    'avg_playtime': round(c['avg_playtime'] or 0,1),
                    'na_ratio': round((c['na_sales'] or 0)/(c['total_sales'] or 1)*100,1),
                    'eu_ratio': round((c['eu_sales'] or 0)/(c['total_sales'] or 1)*100,1),
                    'jp_ratio': round((c['jp_sales'] or 0)/(c['total_sales'] or 1)*100,1),
                }
                country_list.append(d)
            return {'countries':[c['publisher_country'] for c in country_list],'game_counts':[c['game_count'] for c in country_list],'total_sales':[c['total_sales'] for c in country_list],'avg_scores':[c['avg_score'] for c in country_list],'country_list':country_list}
        except Exception as e:
            print(f"获取国家分析失败: {e}"); import traceback; traceback.print_exc()
            return {'countries':[],'game_counts':[],'total_sales':[],'avg_scores':[],'country_list':[]}

    # ============================================================
    # 获奖分析
    # ============================================================
    def get_award_analysis(self):
        """获取获奖游戏分析数据"""
        try:
            awarded = self.games.filter(is_awarded=True)
            not_awarded = self.games.filter(is_awarded=False)
            aw_agg = awarded.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'),max_sales=Max('global_sales'),avg_playtime=Avg('avg_playtime'),avg_language=Avg('language_count'),multiplayer_count=Count('id',filter=Q(multiplayer=True)),dlc_count=Count('id',filter=Q(has_dlc=True)))
            naw_agg = not_awarded.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'),max_sales=Max('global_sales'),avg_playtime=Avg('avg_playtime'),avg_language=Avg('language_count'),multiplayer_count=Count('id',filter=Q(multiplayer=True)),dlc_count=Count('id',filter=Q(has_dlc=True)))
            awarded_stats = {
                'awarded': {k: round(v,2) if isinstance(v,float) else (v or 0) for k,v in aw_agg.items()},
                'not_awarded': {k: round(v,2) if isinstance(v,float) else (v or 0) for k,v in naw_agg.items()},
            }
            award_dist = list(awarded.values('award_count').annotate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score')).order_by('award_count'))
            awarded_by_genre = list(awarded.exclude(genre='').values('genre').annotate(count=Count('id'),avg_sales=Avg('global_sales'),total_sales=Sum('global_sales'),avg_score=Avg('score')).order_by('-count'))
            awarded_by_platform = list(awarded.values('platform').annotate(count=Count('id'),avg_sales=Avg('global_sales'),total_sales=Sum('global_sales')).order_by('-count')[:15])
            awarded_by_year = list(awarded.filter(year__gte=1980).values('year').annotate(count=Count('id'),avg_sales=Avg('global_sales'),total_sales=Sum('global_sales')).order_by('year'))
            return {'awarded_stats':awarded_stats,'award_dist':award_dist,'awarded_by_genre':awarded_by_genre,'awarded_by_platform':awarded_by_platform,'awarded_by_year':awarded_by_year}
        except Exception as e:
            print(f"获取获奖分析失败: {e}"); import traceback; traceback.print_exc()
            return {'awarded_stats':{},'award_dist':[],'awarded_by_genre':[],'awarded_by_platform':[],'awarded_by_year':[]}

    # ============================================================
    # 词云数据生成
    # ============================================================
    def generate_word_cloud_data(self, text_type='name'):
        """生成词云数据，支持: name/genre/publisher/platform/comment"""
        try:
            import jieba; jieba_ok = True
        except ImportError:
            jieba_ok = False
        word_count = Counter()
        stop_words = {'的','了','在','是','和','也','都','有','与','及','到','被','把','上','下','中','对','为','这','那','the','of','and','to','in','a','an','is','it','for','on','with','as','at','by','from','or','The','II','III','IV','vs','VS'}
        if text_type == 'name':
            for name in self.games.values_list('name',flat=True):
                if not name: continue
                if jieba_ok:
                    for w in jieba.cut(name):
                        w=w.strip()
                        if len(w)>=2 and w not in stop_words: word_count[w]+=1
                else:
                    for w in name.split():
                        w=w.strip()
                        if len(w)>=2 and w not in stop_words: word_count[w]+=1
        elif text_type == 'genre':
            word_count = Counter(g for g in self.games.exclude(genre='').values_list('genre',flat=True) if g)
        elif text_type == 'publisher':
            word_count = Counter(p for p in self.games.exclude(publisher='').values_list('publisher',flat=True) if p)
        elif text_type == 'platform':
            word_count = Counter(p for p in self.games.exclude(platform='').values_list('platform',flat=True) if p)
        elif text_type == 'comment':
            for content in self.comments.values_list('content',flat=True)[:5000]:
                if not content: continue
                if jieba_ok:
                    for w in jieba.cut(content):
                        w=w.strip()
                        if len(w)>=2 and w not in stop_words: word_count[w]+=1
                else:
                    for w in content.split():
                        w=w.strip()
                        if len(w)>=2 and w not in stop_words: word_count[w]+=1
        return [{'name':word,'value':count} for word,count in word_count.most_common(150)]

    # ============================================================
    # 情感趋势分析
    # ============================================================
    def get_sentiment_trend_analysis(self):
        """获取评论情感趋势分析数据"""
        try:
            sentiment_stats = {}
            for choice in ['positive','negative','neutral','unknown']:
                sentiment_stats[choice] = self.comments.filter(sentiment=choice).count()
            total_analyzed = sum(v for k,v in sentiment_stats.items() if k!='unknown')
            genre_sentiment = []
            for genre in self.games.exclude(genre='').values_list('genre',flat=True).distinct():
                game_ids = list(self.games.filter(genre=genre).values_list('id',flat=True))
                gc = self.comments.filter(game_id__in=game_ids,sentiment__in=['positive','negative','neutral'])
                total = gc.count()
                if total > 0:
                    pos = gc.filter(sentiment='positive').count()
                    neg = gc.filter(sentiment='negative').count()
                    neu = gc.filter(sentiment='neutral').count()
                    avg_sent = gc.aggregate(avg_score=Avg('sentiment_score'))['avg_score'] or 0
                    genre_sentiment.append({'genre':genre,'total':total,'positive_count':pos,'negative_count':neg,'neutral_count':neu,'positive_rate':round(pos/total*100,1),'negative_rate':round(neg/total*100,1),'neutral_rate':round(neu/total*100,1),'avg_sentiment_score':round(avg_sent,4)})
            genre_sentiment.sort(key=lambda x:x['positive_rate'],reverse=True)
            top = genre_sentiment[:15]
            return {'sentiment_stats':sentiment_stats,'total_analyzed_comments':total_analyzed,'genre_sentiment_list':top,'genre_chart_data':{'genres':[g['genre'] for g in top],'positive_rates':[g['positive_rate'] for g in top],'negative_rates':[g['negative_rate'] for g in top]}}
        except Exception as e:
            print(f"获取情感分析失败: {e}"); import traceback; traceback.print_exc()
            return {'sentiment_stats':{},'total_analyzed_comments':0,'genre_sentiment_list':[],'genre_chart_data':{'genres':[],'positive_rates':[],'negative_rates':[]}}

    # ============================================================
    # 辅助方法
    # ============================================================
    def get_top_games_by_sales(self, limit=10):
        """获取全球销量TOP N游戏"""
        try:
            return [{'id':g.id,'global_rank':g.global_rank,'name':g.name,'platform':g.platform,'genre':g.genre,'publisher':g.publisher,'global_sales':g.global_sales,'na_sales':g.na_sales,'eu_sales':g.eu_sales,'jp_sales':g.jp_sales,'score':g.score,'year':g.year} for g in self.games.filter(global_sales__gt=0).order_by('global_rank')[:limit]]
        except Exception as e:
            print(f"获取畅销游戏失败: {e}"); return []

    def get_regional_comparison(self, game_id):
        """获取单个游戏的地区销量对比数据"""
        try:
            game = Game.objects.get(id=game_id)
            return {'name':game.name,'regions':['北美','欧洲','日本','其他'],'sales':[game.na_sales,game.eu_sales,game.jp_sales,game.other_sales],'total':game.global_sales}
        except Game.DoesNotExist:
            return {}
        except Exception as e:
            print(f"获取地区对比数据失败: {e}"); return {}

    def get_genre_platform_heatmap(self):
        """获取类型-平台热力图数据"""
        try:
            cross = self.games.exclude(genre='').exclude(platform='').values('genre','platform').annotate(count=Count('id'),total_sales=Sum('global_sales')).order_by('-total_sales')
            genres = list(set(d['genre'] for d in cross))
            platforms = list(set(d['platform'] for d in cross))
            data = []
            for d in cross:
                if d['genre'] in genres[:10] and d['platform'] in platforms[:10]:
                    data.append([genres.index(d['genre']),platforms.index(d['platform']),round(d['total_sales'] or 0,2)])
            return {'genres':genres[:10],'platforms':platforms[:10],'data':data}
        except Exception as e:
            print(f"获取热力图数据失败: {e}"); return {'genres':[],'platforms':[],'data':[]}

    def get_multiplayer_analysis(self):
        """获取多人模式分析数据"""
        try:
            mp = self.games.filter(multiplayer=True)
            sp = self.games.filter(multiplayer=False)
            mp_agg = mp.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'))
            sp_agg = sp.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'))
            mp_by_genre = list(mp.exclude(genre='').values('genre').annotate(count=Count('id'),avg_sales=Avg('global_sales')).order_by('-count')[:10])
            return {'multiplayer':{k:round(v,2) if isinstance(v,float) else v for k,v in mp_agg.items()},'singleplayer':{k:round(v,2) if isinstance(v,float) else v for k,v in sp_agg.items()},'mp_by_genre':mp_by_genre}
        except Exception as e:
            print(f"获取多人模式分析失败: {e}"); return {}

    def get_dlc_analysis(self):
        """获取DLC分析数据"""
        try:
            dlc = self.games.filter(has_dlc=True)
            no_dlc = self.games.filter(has_dlc=False)
            dlc_agg = dlc.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'))
            no_dlc_agg = no_dlc.aggregate(count=Count('id'),avg_sales=Avg('global_sales'),avg_score=Avg('score'),total_sales=Sum('global_sales'))
            dlc_by_genre = list(dlc.exclude(genre='').values('genre').annotate(count=Count('id'),avg_sales=Avg('global_sales')).order_by('-count')[:10])
            return {'dlc':{k:round(v,2) if isinstance(v,float) else v for k,v in dlc_agg.items()},'no_dlc':{k:round(v,2) if isinstance(v,float) else v for k,v in no_dlc_agg.items()},'dlc_by_genre':dlc_by_genre}
        except Exception as e:
            print(f"获取DLC分析失败: {e}"); return {}

    def get_playtime_analysis(self):
        """获取游戏时长分析数据"""
        try:
            ranges = {
                '0-5小时': self.games.filter(avg_playtime__gt=0,avg_playtime__lte=5).count(),
                '5-20小时': self.games.filter(avg_playtime__gt=5,avg_playtime__lte=20).count(),
                '20-50小时': self.games.filter(avg_playtime__gt=20,avg_playtime__lte=50).count(),
                '50-100小时': self.games.filter(avg_playtime__gt=50,avg_playtime__lte=100).count(),
                '100小时以上': self.games.filter(avg_playtime__gt=100).count(),
            }
            playtime_vs_sales = list(self.games.filter(avg_playtime__gt=0).values('avg_playtime').annotate(avg_sales=Avg('global_sales'),count=Count('id')).order_by('avg_playtime')[:20])
            return {'ranges':ranges,'playtime_vs_sales':playtime_vs_sales}
        except Exception as e:
            print(f"获取时长分析失败: {e}"); return {'ranges':{},'playtime_vs_sales':[]}


# 创建全局分析实例（单例模式）
_analysis_instance = None

def get_analysis_instance():
    """获取游戏销售数据分析实例"""
    global _analysis_instance
    if _analysis_instance is None:
        _analysis_instance = GameSalesDataAnalysis()
    return _analysis_instance
