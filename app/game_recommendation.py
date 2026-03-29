#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏推荐系统
====================================
基于用户收藏和评论的游戏推荐算法，支持：
- 协同过滤推荐（基于用户收藏和评分相似度）
- 基于内容的推荐（基于游戏类型、平台、发行商匹配）
- 热门游戏推荐（新用户冷启动方案）
- 相似游戏推荐（基于游戏属性匹配度）
"""

import numpy as np
from collections import defaultdict, Counter
import random

from app.models import Game, Comment, User, GameFavorite
from django.db.models import Avg, Count, Sum


class GameRecommendationSystem:
    """
    游戏推荐系统
    
    实现了三种推荐策略：
    1. 协同过滤推荐 - 基于用户之间的收藏和评分相似度
    2. 基于内容推荐 - 基于用户偏好的游戏类型、平台等属性
    3. 热门推荐 - 基于全球销量和评分的热门游戏（冷启动）
    """

    def __init__(self):
        """初始化推荐系统，加载游戏信息和用户数据"""
        self.user_favorites = {}
        self.user_ratings = {}
        self.game_info = {}
        self.load_data()

    def load_data(self):
        """从数据库加载所有游戏信息和用户数据"""
        print("正在加载游戏推荐系统数据...")
        
        # 加载游戏基础信息到内存缓存
        game_count = 0
        for game in Game.objects.all():
            self.game_info[game.id] = {
                'id': game.id,
                'name': game.name,
                'platform': game.platform,
                'genre': game.genre,
                'publisher': game.publisher,
                'publisher_country': game.publisher_country,
                'global_sales': game.global_sales,
                'na_sales': game.na_sales,
                'eu_sales': game.eu_sales,
                'jp_sales': game.jp_sales,
                'score': game.score,
                'release_year': game.release_year,
                'global_rank': game.global_rank,
                'multiplayer': game.multiplayer,
                'has_dlc': game.has_dlc,
                'is_awarded': game.is_awarded,
                'award_count': game.award_count,
                'media_review': game.media_review,
                'player_review': game.player_review,
            }
            game_count += 1

        # 加载用户收藏和评分数据
        self.user_favorites = self._load_user_favorites()
        self.user_ratings = self._load_user_ratings()
        
        print(f"推荐系统加载完成: {game_count}款游戏, "
              f"{len(self.user_favorites)}个有收藏的用户, "
              f"{len(self.user_ratings)}个有评分的用户")

    def refresh_user_data(self):
        """刷新用户收藏和评分数据（保持游戏信息缓存）"""
        old_fav = len(self.user_favorites)
        old_rat = len(self.user_ratings)
        self.user_favorites = self._load_user_favorites()
        self.user_ratings = self._load_user_ratings()
        print(f"用户数据已刷新: 收藏 {old_fav}->{len(self.user_favorites)}, "
              f"评分 {old_rat}->{len(self.user_ratings)}")

    def _load_user_favorites(self):
        """加载用户收藏数据"""
        user_favorites = defaultdict(set)
        local_users = set(User.objects.values_list('username', flat=True))
        favorites = GameFavorite.objects.filter(
            user__username__in=local_users
        ).select_related('user', 'game')
        for fav in favorites:
            user_favorites[fav.user.username].add(fav.game.id)
        return dict(user_favorites)

    def _load_user_ratings(self):
        """加载用户评分数据"""
        user_ratings = defaultdict(dict)
        local_users = set(User.objects.values_list('username', flat=True))
        comments = Comment.objects.filter(
            user__username__in=local_users,
            rating__gt=0
        ).select_related('user', 'game')
        for comment in comments:
            if comment.user and comment.game:
                user_name = comment.user.username
                game_id = comment.game.id
                # 同一用户对同一游戏多次评分取平均
                if game_id in user_ratings[user_name]:
                    old = user_ratings[user_name][game_id]
                    user_ratings[user_name][game_id] = (old + comment.rating) / 2
                else:
                    user_ratings[user_name][game_id] = comment.rating
        return dict(user_ratings)

    # ============================================================
    # 协同过滤推荐
    # ============================================================
    def collaborative_filtering_recommendations(self, target_user, top_n=12):
        """
        基于用户协同过滤的推荐算法
        结合收藏和评分数据，计算用户间相似度，推荐相似用户喜欢的游戏
        
        Args:
            target_user: 目标用户名
            top_n: 推荐游戏数量
        Returns:
            推荐的游戏列表
        """
        # 冷启动处理：新用户返回热门推荐
        if target_user not in self.user_favorites and target_user not in self.user_ratings:
            return self.get_popular_games(top_n)

        target_favs = self.user_favorites.get(target_user, set())
        target_ratings = self.user_ratings.get(target_user, {})
        similarity_scores = {}

        # 计算与所有其他用户的相似度
        all_users = set(list(self.user_favorites.keys()) + list(self.user_ratings.keys()))
        for user_name in all_users:
            if user_name == target_user:
                continue

            user_favs = self.user_favorites.get(user_name, set())
            user_ratings = self.user_ratings.get(user_name, {})

            # 计算收藏相似度（Jaccard系数）
            fav_sim = 0.0
            if target_favs and user_favs:
                common = target_favs & user_favs
                if common:
                    union = target_favs | user_favs
                    fav_sim = len(common) / len(union)

            # 计算评分相似度（皮尔逊相关系数）
            rating_sim = 0.0
            if target_ratings and user_ratings:
                common_games = set(target_ratings.keys()) & set(user_ratings.keys())
                if len(common_games) >= 2:
                    t_ratings = [target_ratings[gid] for gid in common_games]
                    u_ratings = [user_ratings[gid] for gid in common_games]
                    try:
                        corr = np.corrcoef(t_ratings, u_ratings)[0, 1]
                        if not np.isnan(corr):
                            rating_sim = max(0, corr)  # 只取正相关
                    except:
                        pass

            # 综合相似度（收藏权重0.6，评分权重0.4）
            combined = fav_sim * 0.6 + rating_sim * 0.4
            if combined > 0:
                similarity_scores[user_name] = combined

        # 按相似度排序，取最相似的用户
        sorted_users = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)

        # 收集推荐游戏及其得分
        game_scores = defaultdict(float)
        game_sources = defaultdict(list)

        for similar_user, sim in sorted_users[:20]:
            # 从收藏中推荐
            sim_favs = self.user_favorites.get(similar_user, set())
            for game_id in sim_favs:
                if game_id not in target_favs and game_id in self.game_info:
                    game_scores[game_id] += sim
                    game_sources[game_id].append((similar_user, sim, 'favorite'))

            # 从高评分中推荐
            sim_ratings = self.user_ratings.get(similar_user, {})
            for game_id, rating in sim_ratings.items():
                if rating >= 4.0 and game_id not in target_favs:
                    if game_id not in target_ratings and game_id in self.game_info:
                        weighted = sim * (rating / 5.0)
                        game_scores[game_id] += weighted
                        game_sources[game_id].append((similar_user, sim, 'rating'))

        # 排序并构造结果
        sorted_games = sorted(game_scores.items(), key=lambda x: x[1], reverse=True)
        result = []
        for game_id, score in sorted_games[:top_n]:
            if game_id in self.game_info:
                game_data = self.game_info[game_id].copy()
                game_data['recommendation_score'] = round(score, 3)
                game_data['recommendation_type'] = 'collaborative'
                game_data['recommending_users_count'] = len(game_sources[game_id])
                result.append(game_data)

        # 如果推荐数量不足，用热门游戏补充
        if len(result) < top_n:
            existing_ids = {g['id'] for g in result}
            popular = self.get_popular_games(top_n - len(result), exclude_ids=existing_ids)
            result.extend(popular)

        return result[:top_n]

    # ============================================================
    # 基于内容的推荐
    # ============================================================
    def content_based_recommendations(self, target_user, top_n=12):
        """
        基于内容的推荐算法
        分析用户收藏游戏的类型、平台等特征，推荐相似的游戏
        """
        if target_user not in self.user_favorites:
            return []

        target_favs = self.user_favorites[target_user]

        # 分析用户偏好
        genre_prefs = Counter()
        platform_prefs = Counter()
        publisher_prefs = Counter()
        year_prefs = []

        for game_id in target_favs:
            if game_id in self.game_info:
                game = self.game_info[game_id]
                if game['genre']:
                    genre_prefs[game['genre']] += 1
                if game['platform']:
                    platform_prefs[game['platform']] += 1
                if game['publisher']:
                    publisher_prefs[game['publisher']] += 1
                if game['release_year'] and game['release_year'] > 0:
                    year_prefs.append(game['release_year'])

        # 计算平均偏好年份
        avg_year = sum(year_prefs) / len(year_prefs) if year_prefs else 2010

        # 为候选游戏评分
        candidates = []
        for game_id, game_info in self.game_info.items():
            if game_id in target_favs:
                continue

            score = 0.0

            # 类型匹配（最重要）
            if game_info['genre'] in genre_prefs:
                score += genre_prefs[game_info['genre']] * 0.4

            # 平台匹配
            if game_info['platform'] in platform_prefs:
                score += platform_prefs[game_info['platform']] * 0.2

            # 发行商匹配
            if game_info['publisher'] in publisher_prefs:
                score += publisher_prefs[game_info['publisher']] * 0.15

            # 年份接近度（越接近用户偏好年份加分越多）
            if game_info['release_year'] and game_info['release_year'] > 0:
                year_diff = abs(game_info['release_year'] - avg_year)
                if year_diff <= 3:
                    score += 0.1
                elif year_diff <= 5:
                    score += 0.05

            # 高评分加成
            if game_info['score'] and game_info['score'] >= 8.0:
                score += 0.1

            if score > 0:
                game_copy = game_info.copy()
                game_copy['content_score'] = round(score, 3)
                game_copy['recommendation_type'] = 'content_based'
                candidates.append(game_copy)

        # 按得分排序
        candidates.sort(key=lambda x: x['content_score'], reverse=True)
        return candidates[:top_n]

    # ============================================================
    # 热门游戏推荐
    # ============================================================
    def get_popular_games(self, top_n=12, randomize=True, exclude_ids=None):
        """
        获取热门游戏推荐（用于新用户或补充推荐）
        基于全球销量和评分，带有随机化因素避免推荐总是相同
        """
        exclude_ids = exclude_ids or set()
        popular = []

        games_query = Game.objects.filter(
            global_sales__gte=1.0
        ).exclude(
            id__in=exclude_ids
        ).order_by('global_rank')

        if randomize:
            games = list(games_query[:top_n * 3])
            if len(games) > top_n:
                games = random.sample(games, min(len(games), top_n * 2))
        else:
            games = list(games_query[:top_n * 2])

        for game in games:
            popular.append({
                'id': game.id,
                'name': game.name,
                'platform': game.platform,
                'genre': game.genre,
                'publisher': game.publisher,
                'global_sales': game.global_sales,
                'score': game.score,
                'release_year': game.release_year,
                'global_rank': game.global_rank,
                'multiplayer': game.multiplayer,
                'is_awarded': game.is_awarded,
                'recommendation_type': 'popular'
            })

        if randomize and len(popular) > top_n:
            random.shuffle(popular)

        return popular[:top_n]

    # ============================================================
    # 综合推荐入口
    # ============================================================
    def get_recommendations_for_user(self, user_name, top_n=12):
        """
        为特定用户生成综合推荐
        
        策略：
        1. 先尝试协同过滤推荐
        2. 如果数量不够，补充基于内容的推荐
        3. 最后用热门游戏填满
        """
        # 先获取协同过滤推荐
        cf_recs = self.collaborative_filtering_recommendations(user_name, top_n)
        
        if len(cf_recs) >= top_n:
            return cf_recs[:top_n]
        
        # 补充基于内容的推荐
        existing_ids = {g['id'] for g in cf_recs}
        content_recs = self.content_based_recommendations(user_name, top_n)
        for rec in content_recs:
            if rec['id'] not in existing_ids:
                cf_recs.append(rec)
                existing_ids.add(rec['id'])
            if len(cf_recs) >= top_n:
                break
        
        # 最后用热门游戏填满
        if len(cf_recs) < top_n:
            popular = self.get_popular_games(top_n - len(cf_recs), exclude_ids=existing_ids)
            cf_recs.extend(popular)
        
        return cf_recs[:top_n]

    # ============================================================
    # 相似游戏推荐
    # ============================================================
    def get_similar_games(self, game_id, top_n=6):
        """
        基于游戏内容属性的相似游戏推荐
        考虑类型、平台、发行商、年份等多维度相似性
        """
        if game_id not in self.game_info:
            return []

        target = self.game_info[game_id]
        similar = []

        for gid, game in self.game_info.items():
            if gid == game_id:
                continue

            score = 0.0

            # 类型相似度（权重最高）
            if game['genre'] == target['genre'] and game['genre']:
                score += 0.4

            # 平台相似度
            if game['platform'] == target['platform'] and game['platform']:
                score += 0.25

            # 发行商相似度
            if game['publisher'] == target['publisher'] and game['publisher']:
                score += 0.15

            # 年份接近度
            if game['release_year'] and target['release_year'] and game['release_year'] > 0 and target['release_year'] > 0:
                year_diff = abs(game['release_year'] - target['release_year'])
                if year_diff <= 2:
                    score += 0.1
                elif year_diff <= 5:
                    score += 0.05

            # 评分接近度
            if game['score'] and target['score'] and game['score'] > 0 and target['score'] > 0:
                score_diff = abs(game['score'] - target['score'])
                if score_diff <= 1.0:
                    score += 0.1

            if score > 0:
                g_copy = game.copy()
                g_copy['similarity_score'] = round(score, 2)
                g_copy['recommendation_type'] = 'similar_content'
                similar.append(g_copy)

        # 按相似度和销量双重排序
        similar.sort(key=lambda x: (x['similarity_score'], x['global_sales']), reverse=True)
        return similar[:top_n]

    # ============================================================
    # 用户收藏统计
    # ============================================================
    def get_user_favorite_stats(self, user_name):
        """获取用户收藏统计信息"""
        try:
            user = User.objects.get(username=user_name)

            total_favorites = GameFavorite.objects.filter(user=user).count()

            # 收藏的游戏类型统计
            genre_stats = GameFavorite.objects.filter(user=user).values(
                'game__genre'
            ).annotate(count=Count('game__genre')).order_by('-count')

            # 收藏的平台统计
            platform_stats = GameFavorite.objects.filter(user=user).values(
                'game__platform'
            ).annotate(count=Count('game__platform')).order_by('-count')

            # 收藏的发行商统计
            publisher_stats = GameFavorite.objects.filter(user=user).values(
                'game__publisher'
            ).annotate(count=Count('game__publisher')).order_by('-count')

            # 最近收藏
            recent = GameFavorite.objects.filter(user=user).order_by('-created_time')[:5]

            return {
                'total_favorites': total_favorites,
                'favorite_genres': list(genre_stats[:10]),
                'favorite_platforms': list(platform_stats[:10]),
                'favorite_publishers': list(publisher_stats[:10]),
                'recent_favorites': [
                    {
                        'game_name': fav.game.name,
                        'game_id': fav.game.id,
                        'created_time': fav.created_time,
                        'platform': fav.game.platform,
                        'genre': fav.game.genre,
                    }
                    for fav in recent
                ]
            }
        except User.DoesNotExist:
            return {
                'total_favorites': 0,
                'favorite_genres': [],
                'favorite_platforms': [],
                'favorite_publishers': [],
                'recent_favorites': []
            }


# 创建全局推荐系统实例（单例模式）
_recommendation_system = None

def get_recommendation_system(force_refresh=True):
    """获取推荐系统实例，可选择是否刷新用户数据"""
    global _recommendation_system
    if _recommendation_system is None:
        _recommendation_system = GameRecommendationSystem()
    elif force_refresh:
        _recommendation_system.refresh_user_data()
    return _recommendation_system
