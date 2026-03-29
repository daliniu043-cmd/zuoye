from django import template

register = template.Library()





@register.filter
def format_price(price):
    """格式化价格显示"""
    if not price or price == '0' or price == 0:
        return '免费'
    try:
        price_float = float(price)
        if price_float == 0:
            return '免费'
        return f"¥{price_float:.2f}"
    except (ValueError, TypeError):
        return price or '未知'

@register.filter
def format_rating_count(count):
    """格式化评分数量显示"""
    if not count:
        return '0'
    try:
        count = int(count)
        if count < 1000:
            return str(count)
        elif count < 10000:
            return f"{count / 1000:.1f}K"
        elif count < 1000000:
            return f"{count / 10000:.1f}万"
        else:
            return f"{count / 1000000:.1f}M"
    except (ValueError, TypeError):
        return str(count)

@register.filter
def format_comment_time(comment):
    """格式化评论时间显示"""
    # 优先使用comment_time字段
    if comment.comment_time and comment.comment_time.strip():
        return comment.comment_time

    # 如果comment_time为空，尝试使用comment_timestamp
    if comment.comment_timestamp and comment.comment_timestamp > 0:
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(comment.comment_timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')  # 带年份的完整格式
        except (ValueError, OSError):
            pass

    # 最后使用create_time
    if hasattr(comment, 'create_time') and comment.create_time:
        return comment.create_time.strftime('%Y-%m-%d %H:%M')  # 带年份的完整格式

    return '未知时间'

@register.filter
def split(value, delimiter=','):
    """分割字符串为列表"""
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]
