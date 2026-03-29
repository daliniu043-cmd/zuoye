from django.db import models


class User(models.Model):
    """用户模型"""
    id = models.AutoField('id', primary_key=True)
    username = models.CharField('用户名', max_length=255, default='')
    password = models.CharField('密码', max_length=255, default='')
    sex = models.CharField('性别', max_length=255, default='')
    address = models.CharField('地址', max_length=255, default='')
    avatar = models.FileField('头像', upload_to='avatar', default='avatar/default.png')
    textarea = models.CharField('个人简介', max_length=255, default='这个人很懒，什么都没写...')
    createTime = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "前台用户"
        verbose_name = "前台用户"

    def __str__(self):
        return self.username


class Game(models.Model):
    """游戏销售数据模型 - 对应VVgsales数据集"""
    id = models.AutoField('游戏ID', primary_key=True)
    global_rank = models.IntegerField('全球销售排名', default=0)
    name = models.CharField('游戏名称', max_length=500, default='')
    platform = models.CharField('游戏平台', max_length=50, default='')
    release_year = models.IntegerField('发行年份', default=0, null=True, blank=True)
    genre = models.CharField('游戏类型', max_length=100, default='')
    publisher = models.CharField('发行商', max_length=500, default='')
    publisher_country = models.CharField('发行商所属国家', max_length=100, default='', blank=True)
    na_sales = models.FloatField('北美地区销量', default=0.0, help_text='单位：百万份')
    eu_sales = models.FloatField('欧洲地区销量', default=0.0, help_text='单位：百万份')
    jp_sales = models.FloatField('日本地区销量', default=0.0, help_text='单位：百万份')
    other_sales = models.FloatField('其他地区销量', default=0.0, help_text='单位：百万份')
    global_sales = models.FloatField('全球总销量', default=0.0, help_text='单位：百万份')
    score = models.FloatField('游戏评分', default=0.0, help_text='满分10分')
    avg_playtime = models.IntegerField('人均游戏时长', default=0, help_text='单位：小时')
    multiplayer = models.BooleanField('多人模式支持', default=False)
    has_dlc = models.BooleanField('是否有DLC', default=False)
    media_review = models.CharField('媒体评价', max_length=50, default='')
    player_review = models.CharField('玩家口碑', max_length=50, default='')
    is_awarded = models.BooleanField('是否获奖', default=False)
    award_count = models.IntegerField('获奖数量', default=0)
    language_count = models.IntegerField('游戏语言数量', default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name_plural = "游戏销售数据"
        verbose_name = "游戏销售数据"
        db_table = 'game'
        ordering = ['global_rank']

    def __str__(self):
        return self.name


class Comment(models.Model):
    """评论模型"""
    id = models.AutoField('评论ID', primary_key=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='关联游戏', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='评论用户', null=True, blank=True)
    user_name = models.CharField('用户名', max_length=200, default='')
    avatar_url = models.URLField('用户头像', max_length=500, default='', blank=True)
    content = models.TextField('评论内容', default='')
    rating = models.FloatField('用户评分', default=0.0, help_text='1-5分')
    like_count = models.IntegerField('点赞数', default=0)
    reply_count = models.IntegerField('回复数', default=0)
    comment_time = models.CharField('评论时间', max_length=100, default='')
    comment_timestamp = models.BigIntegerField('评论时间戳', default=0)
    SENTIMENT_CHOICES = [
        ('positive', '积极'),
        ('negative', '消极'),
        ('neutral', '中性'),
        ('unknown', '未知'),
    ]
    sentiment = models.CharField('情感倾向', max_length=20, choices=SENTIMENT_CHOICES, default='unknown')
    sentiment_score = models.FloatField('情感得分', default=0.0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "游戏评论"
        verbose_name = "游戏评论"
        db_table = 'comment'

    def __str__(self):
        if self.game:
            return f"{self.game.name} - {self.user_name}"
        return f"评论 - {self.user_name}"


class GameFavorite(models.Model):
    """游戏收藏模型"""
    id = models.AutoField('ID', primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='游戏')
    created_time = models.DateTimeField('收藏时间', auto_now_add=True)
    notes = models.TextField('收藏备注', default='', blank=True, max_length=500)

    class Meta:
        verbose_name_plural = "游戏收藏"
        verbose_name = "游戏收藏"
        db_table = 'game_favorites'
        unique_together = ('user', 'game')
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.user.username} - {self.game.name}"
