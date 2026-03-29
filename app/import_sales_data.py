#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入VVgsales数据集到数据库，并自动生成评论数据
确保游戏16598条 + 评论至少4000条 = 总计超过20000条记录
"""
import os
import sys
import random
import django
from datetime import datetime, timedelta

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meng.settings')
django.setup()

from app.models import Game, Comment


def import_vvgsales(file_path):
    """从Excel文件导入游戏销售数据"""
    import openpyxl
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb['Sheet1']

    games_created = 0
    games_updated = 0

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if not row[1]:  # 跳过无名称的行
            continue
        try:
            game, created = Game.objects.update_or_create(
                global_rank=int(row[0] or 0),
                name=str(row[1] or ''),
                platform=str(row[2] or ''),
                defaults={
                    'release_year': int(row[3]) if row[3] else 0,
                    'genre': str(row[4] or ''),
                    'publisher': str(row[5] or ''),
                    'publisher_country': str(row[6] or ''),
                    'na_sales': float(row[7] or 0),
                    'eu_sales': float(row[8] or 0),
                    'jp_sales': float(row[9] or 0),
                    'other_sales': float(row[10] or 0),
                    'global_sales': float(row[11] or 0),
                    'score': float(row[12] or 0),
                    'avg_playtime': int(row[13] or 0),
                    'multiplayer': bool(row[14]),
                    'has_dlc': bool(row[15]),
                    'media_review': str(row[16] or ''),
                    'player_review': str(row[17] or ''),
                    'is_awarded': bool(row[18]),
                    'award_count': int(row[19] or 0),
                    'language_count': int(row[20] or 0),
                }
            )
            if created:
                games_created += 1
            else:
                games_updated += 1

            if (games_created + games_updated) % 1000 == 0:
                print(f"  已处理 {games_created + games_updated} 条游戏数据...")

        except Exception as e:
            print(f"  导入第{i+2}行失败: {e}")
            continue

    print(f"游戏数据导入完成: 新增 {games_created}, 更新 {games_updated}")
    return games_created + games_updated


def generate_comments(target_count=4500):
    """自动生成评论数据，确保总记录数超过20000"""
    existing_comments = Comment.objects.count()
    need_count = max(0, target_count - existing_comments)
    if need_count == 0:
        print(f"评论数据已足够 ({existing_comments} 条)，跳过生成")
        return existing_comments

    print(f"现有评论 {existing_comments} 条，需生成 {need_count} 条...")

    # 取销量前1000的游戏来分配评论
    top_games = list(Game.objects.order_by('-global_sales')[:1000].values_list('id', 'name', 'genre', 'score'))
    if not top_games:
        print("没有游戏数据，无法生成评论")
        return 0

    # 评论模板
    positive_templates = [
        "这款游戏太棒了，玩了很久都不腻！", "经典之作，强烈推荐！",
        "画面精美，玩法有趣，值得一玩", "剧情感人，音乐好听，满分推荐",
        "和朋友一起玩超级有趣！", "童年回忆，经典永不过时",
        "操作流畅，关卡设计精妙", "非常好玩的游戏，停不下来",
        "游戏性很强，可玩性高", "制作精良，诚意满满的作品",
        "画风很喜欢，玩法也很创新", "这游戏真的太好玩了",
        "节奏感很好，越玩越上头", "细节做得很到位，好评",
        "剧情丰富，人物刻画深入", "配乐非常赞，沉浸感很强",
        "关卡设计很有想象力", "操作简单但策略性很强",
        "耐玩度很高，反复游玩也不腻", "这种类型的巅峰之作",
    ]
    negative_templates = [
        "画面太粗糙了，不太好玩", "剧情太短了，感觉不值",
        "操作不太流畅，有些卡顿", "内容太少了，期待更新",
        "难度设计不合理，太难了", "重复度太高，玩一会就腻了",
        "bug太多了，体验很差", "优化不好，经常闪退",
        "玩法比较单一，缺乏创新", "对比同类型游戏有些逊色",
    ]
    neutral_templates = [
        "还行吧，中规中矩", "一般般，打发时间还可以",
        "有优点也有缺点，总体还行", "不算太好也不算太差",
        "玩了一会，感觉一般", "还可以，但没有特别惊艳",
    ]

    usernames = [f"玩家{i}" for i in range(1, 201)] + [
        "游戏达人", "快乐小玩家", "硬核玩家", "休闲游戏迷", "经典游戏粉",
        "评测大师", "游戏收藏家", "怀旧玩家", "挑战者", "探索者",
    ]

    comments_to_create = []
    base_time = datetime(2024, 1, 1)

    for idx in range(need_count):
        game_id, game_name, genre, score = random.choice(top_games)

        # 根据游戏评分决定评论倾向
        rand = random.random()
        if score >= 7:
            if rand < 0.6:
                content = random.choice(positive_templates)
                rating = random.uniform(3.5, 5.0)
                sentiment = 'positive'
            elif rand < 0.85:
                content = random.choice(neutral_templates)
                rating = random.uniform(2.5, 3.5)
                sentiment = 'neutral'
            else:
                content = random.choice(negative_templates)
                rating = random.uniform(1.0, 2.5)
                sentiment = 'negative'
        elif score >= 5:
            if rand < 0.35:
                content = random.choice(positive_templates)
                rating = random.uniform(3.0, 4.5)
                sentiment = 'positive'
            elif rand < 0.7:
                content = random.choice(neutral_templates)
                rating = random.uniform(2.0, 3.5)
                sentiment = 'neutral'
            else:
                content = random.choice(negative_templates)
                rating = random.uniform(1.0, 2.5)
                sentiment = 'negative'
        else:
            if rand < 0.2:
                content = random.choice(positive_templates)
                rating = random.uniform(2.5, 4.0)
                sentiment = 'positive'
            elif rand < 0.5:
                content = random.choice(neutral_templates)
                rating = random.uniform(1.5, 3.0)
                sentiment = 'neutral'
            else:
                content = random.choice(negative_templates)
                rating = random.uniform(1.0, 2.0)
                sentiment = 'negative'

        # 加上游戏名称使评论更自然
        if random.random() < 0.3:
            content = f"【{game_name[:20]}】" + content

        comment_date = base_time + timedelta(
            days=random.randint(0, 400),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        comments_to_create.append(Comment(
            game_id=game_id,
            user_name=random.choice(usernames),
            content=content,
            rating=round(rating, 1),
            like_count=random.randint(0, 500),
            reply_count=random.randint(0, 50),
            comment_time=comment_date.strftime('%Y-%m-%d %H:%M'),
            comment_timestamp=int(comment_date.timestamp()),
            sentiment=sentiment,
            sentiment_score=round(random.uniform(-1, 1) if sentiment == 'neutral' else
                                  (random.uniform(0.2, 1.0) if sentiment == 'positive' else
                                   random.uniform(-1.0, -0.2)), 3),
        ))

        if len(comments_to_create) >= 500:
            Comment.objects.bulk_create(comments_to_create)
            print(f"  已生成 {idx + 1}/{need_count} 条评论...")
            comments_to_create = []

    if comments_to_create:
        Comment.objects.bulk_create(comments_to_create)

    total = Comment.objects.count()
    print(f"评论生成完成，当前共 {total} 条评论")
    return total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='导入VVgsales数据')
    parser.add_argument('--file', default='VVgsales_3_.xlsx', help='Excel文件路径')
    parser.add_argument('--comments', type=int, default=4500, help='目标评论数量')
    args = parser.parse_args()

    print("=" * 60)
    print("游戏销售数据导入工具")
    print("=" * 60)

    # 导入游戏数据
    print("\n[1/2] 导入游戏销售数据...")
    game_count = import_vvgsales(args.file)

    # 生成评论
    print(f"\n[2/2] 生成评论数据 (目标: {args.comments} 条)...")
    comment_count = generate_comments(args.comments)

    total = game_count + comment_count
    print(f"\n{'=' * 60}")
    print(f"导入完成! 游戏: {game_count}, 评论: {comment_count}, 总计: {total}")
    print(f"{'=' * 60}")
