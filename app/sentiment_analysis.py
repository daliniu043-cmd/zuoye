#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import jieba
from collections import Counter

class SentimentAnalyzer:
    """中文评论情感分析器"""
    
    def __init__(self):
        # 扩展的积极词汇（电影评论专用）
        self.positive_words = {
            # 基础积极词
            '好', '棒', '赞', '喜欢', '爱', '优秀', '精彩', '完美', '出色', '杰出', 
            '惊艳', '感动', '震撼', '经典', '值得', '推荐', '满意', '开心', '快乐',
            '有趣', '幽默', '搞笑', '温暖', '治愈', '美好', '深刻', '感人', '励志',
            '激动', '兴奋', '期待', '神作', '佳作', '巨作', '名作', '杰作', '力作',
            '惊喜', '惊艳', '惊叹', '佩服', '钦佩', '崇拜', '心动', '舒服', '享受',
            '满足', '幸福', '甜蜜', '浪漫', '唯美', '绚烂', '华丽', '壮观', '震撼',
            
            # 网络流行语
            '牛', '6', '666', '厉害', '强', '顶', '支持', '给力', '靠谱', '走心',
            'yyds', '绝绝子', '太棒了', '爱了', '慕了', '绝了', '妙啊', '牛逼',
            
            # 电影专业词汇 - 积极
            '演技好', '演技棒', '演技精湛', '演技自然', '演技在线', '演得好',
            '剧情好', '剧情棒', '剧情精彩', '剧情紧凑', '剧情流畅', '故事好',
            '画面美', '画面棒', '画面精美', '画面唯美', '镜头美', '构图好',
            '音乐好', '配乐棒', '音效好', '音响效果好', '声音好听',
            '特效好', '特效棒', '特效精彩', '特效逼真', '视效好', '制作精良',
            '导演功力', '导演水平', '导演厉害', '执导', '拍得好', '制作用心',
            '台词好', '对白精彩', '配音好', '声优棒', 'dubbing好',
            '节奏好', '节奏紧凑', '节奏适中', '节奏掌控', '张弛有度',
            
            # 观影感受词汇
            '看哭了', '看燃了', '看爽了', '看嗨了', '看完想二刷', '想推荐',
            '值回票价', '不虚此行', '意犹未尽', '回味无穷', '印象深刻',
            '五星', '满分', '高分', '好评', '力荐', '必看', '佳片',
            
            # 情感表达
            '感动到哭', '笑死我了', '太有意思', '超级好看', '相见恨晚',
            '百看不厌', '经久不衰', '永恒经典', '时代佳作', '划时代'
        }
        
        # 扩展的消极词汇（电影评论专用）
        self.negative_words = {
            # 基础消极词
            '差', '烂', '垃圾', '无聊', '失望', '难看', '糟糕', '恶心', '讨厌', '愤怒',
            '生气', '郁闷', '沮丧', '悲伤', '痛苦', '伤心', '难过', '后悔', '可惜',
            '遗憾', '尴尬', '别扭', '不爽', '恶劣', '粗糙', '拖沓', '冗长', '混乱',
            '无聊', '乏味', '平庸', '幼稚', '弱智', '智障', '脑残', '瞎', '盲',
            '败笔', '毒瘤', '灾难', '噩梦', '折磨', '煎熬', '浪费', '坑', '雷',
            '狗血', '老套', '俗套', '套路', '做作', '矫情', '装逼', '炫技', '卖弄',
            '拖累', '累赘', '负担', '麻烦', '问题', '毛病', '缺陷', '弊端', '漏洞',
            
            # 网络流行语 - 消极
            '拉胯', '翻车', '崩了', '毁了', '废了', '凉了', '糊了', '扑街',
            '辣眼睛', '智商下线', '三观不正', '恶心到了', '槽点满满',
            
            # 电影专业词汇 - 消极
            '演技差', '演技烂', '演技尴尬', '演技生硬', '演技下线', '演技崩坏',
            '剧情烂', '剧情差', '剧情无聊', '剧情拖沓', '剧情混乱', '故事烂',
            '画面差', '画面烂', '画面粗糙', '画面简陋', '镜头乱', '构图差',
            '音乐差', '配乐烂', '音效差', '音响效果差', '声音难听',
            '特效差', '特效烂', '特效假', '特效廉价', '视效差', '制作粗糙',
            '导演水平差', '导演不行', '拍得烂', '制作敷衍', '毫无诚意',
            '台词差', '对白尴尬', '配音差', '声优烂', 'dubbing差',
            '节奏差', '节奏拖沓', '节奏混乱', '节奏失控', '冗长无味',
            
            # 观影感受词汇 - 消极
            '看睡着了', '看不下去', '想退票', '浪费时间', '浪费金钱',
            '不值票价', '白跑一趟', '后悔观看', '印象极差',
            '一星', '零分', '低分', '差评', '不推荐', '慎看', '烂片',
            
            # 情感表达 - 消极
            '气死我了', '无语了', '太无聊了', '超级难看', '早知道不看',
            '看了想吐', '浪费生命', '史上最烂', '年度最差', '最大败笔'
        }
        
        # 扩展的程度副词权重
        self.degree_words = {
            # 强程度副词
            '非常': 2.0, '特别': 2.0, '十分': 2.0, '相当': 1.8, '极其': 2.8,
            '无比': 3.0, '绝对': 2.8, '完全': 2.5, '彻底': 2.5, '简直': 2.3,
            '超级': 2.5, '巨': 2.5, '超': 2.5, '极': 2.8, '狂': 2.3,
            
            # 中等程度副词
            '很': 1.5, '挺': 1.3, '蛮': 1.3, '真的': 1.8, '确实': 1.8,
            '的确': 1.8, '实在': 1.8, '太': 2.0, '好': 1.2, '还': 1.1,
            
            # 轻度程度副词
            '比较': 1.2, '稍微': 0.8, '有点': 0.9, '一点': 0.8, '略': 0.7,
            '些许': 0.8, '微': 0.7, '较': 1.1, '相对': 1.0, '算是': 0.9
        }
        
        # 扩展的否定词
        self.negation_words = {
            '不', '没', '无', '非', '未', '别', '休', '毋', '莫', '勿', '并非',
            '不是', '没有', '不会', '不能', '不要', '不用', '不必', '不够',
            '从不', '从未', '从来不', '决不', '绝不', '永不', '难以', '无法',
            '不可能', '不应该', '不值得', '不推荐', '不建议', '不看好'
        }
        
        # 转折词（表示语义转向）
        self.transition_words = {
            '但是': -0.8, '不过': -0.8, '然而': -0.8, '可是': -0.8, '却': -0.7,
            '只是': -0.6, '就是': -0.5, '虽然': -0.6, '尽管': -0.6, '虽说': -0.6,
            '话说': -0.4, '说实话': -0.3, '老实说': -0.3, '坦白说': -0.3
        }
        
        # 情感表情符号
        self.emoji_positive = {'😊', '😍', '👍', '❤️', '💕', '😘', '🥰', '😁', '😄', '😆', '🤗', '👏', '🙌', '✨', '🌟', '⭐'}
        self.emoji_negative = {'😭', '😢', '😡', '😠', '💔', '👎', '😞', '😔', '😤', '🤬', '😰', '😨', '💀', '☠️', '🤮', '🙄'}

    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        
        # 去除多余空格和换行
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 保留中文、英文、数字、表情和基本标点
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()（），。！？；：""''《》【】\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
        
        return text

    def extract_features(self, text):
        """提取文本特征"""
        features = {
            'positive_count': 0,
            'negative_count': 0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'emoji_positive': 0,
            'emoji_negative': 0,
            'exclamation_count': text.count('!') + text.count('！'),
            'question_count': text.count('?') + text.count('？'),
            'length': len(text),
            'rating_numbers': [],
            'transition_impact': 0.0
        }
        
        # 统计情感表情符号
        for char in text:
            if char in self.emoji_positive:
                features['emoji_positive'] += 1
            elif char in self.emoji_negative:
                features['emoji_negative'] += 1
        
        # 提取评分数字（如"8分"、"9.5分"、"五星"等）
        rating_patterns = [
            r'(\d+(?:\.\d+)?)分',  # 数字分
            r'(\d+(?:\.\d+)?)星',  # 数字星
            r'(五|四|三|二|一)星',  # 中文星级
            r'满分.*?(\d+)',      # 满分X分
            r'(\d+)\/(\d+)',      # X/Y评分
            r'(\d+)\/10'          # X/10评分
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    features['rating_numbers'].extend([float(m) for m in match if m.replace('.', '').isdigit()])
                else:
                    if match in ['五', '四', '三', '二', '一']:
                        features['rating_numbers'].append({'五': 5, '四': 4, '三': 3, '二': 2, '一': 1}[match])
                    elif match.replace('.', '').isdigit():
                        features['rating_numbers'].append(float(match))
        
        # 检测转折词影响
        for word, impact in self.transition_words.items():
            if word in text:
                features['transition_impact'] += impact
        
        return features

    def analyze_words(self, text):
        """增强的词汇情感分析"""
        try:
            # 使用jieba分词
            words = list(jieba.cut(text))
        except:
            # 如果jieba不可用，使用简单分词
            words = text.split()
        
        positive_score = 0.0
        negative_score = 0.0
        
        # 转换为句子列表进行分析（按标点分割）
        sentences = re.split(r'[。！？.!?;；]', text)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            try:
                sentence_words = list(jieba.cut(sentence))
            except:
                sentence_words = sentence.split()
            sentence_positive = 0.0
            sentence_negative = 0.0
            has_transition = False
            
            # 检查句子中是否有转折词
            for word in self.transition_words:
                if word in sentence:
                    has_transition = True
                    break
            
            i = 0
            while i < len(sentence_words):
                word = sentence_words[i].strip()
                if not word:
                    i += 1
                    continue
                
                # 检查是否有程度副词（扩展搜索范围）
                degree = 1.0
                for j in range(max(0, i-2), i):  # 检查前2个词
                    if sentence_words[j].strip() in self.degree_words:
                        degree = max(degree, self.degree_words[sentence_words[j].strip()])
                
                # 检查是否有否定词（扩展搜索范围）
                negation = False
                negation_count = 0
                for j in range(max(0, i-3), i):  # 检查前3个词
                    if sentence_words[j].strip() in self.negation_words:
                        negation_count += 1
                
                # 双重否定变肯定
                negation = negation_count % 2 == 1
                
                # 检查组合词汇（如"演技好"、"剧情棒"等）
                combined_word = ""
                if i > 0:
                    combined_word = sentence_words[i-1].strip() + word
                
                # 计算情感得分
                base_score = 1.0
                found_sentiment = False
                
                # 优先检查组合词
                if combined_word in self.positive_words or combined_word in self.negative_words:
                    word = combined_word
                    found_sentiment = True
                elif word in self.positive_words or word in self.negative_words:
                    found_sentiment = True
                
                if found_sentiment:
                    # 根据词汇长度调整权重（复合词汇权重更高）
                    if len(word) > 2:
                        base_score *= 1.3
                    
                    final_score = base_score * degree
                    
                    if word in self.positive_words:
                        if negation:
                            sentence_negative += final_score
                        else:
                            sentence_positive += final_score
                    elif word in self.negative_words:
                        if negation:
                            sentence_positive += final_score
                        else:
                            sentence_negative += final_score
                
                i += 1
            
            # 如果有转折词，调整前半句的权重
            if has_transition:
                # 找到转折词位置
                transition_pos = -1
                for word in self.transition_words:
                    pos = sentence.find(word)
                    if pos != -1:
                        transition_pos = pos
                        break
                
                if transition_pos != -1:
                    # 转折词前的情感权重降低，转折词后的权重提高
                    before_part = sentence[:transition_pos]
                    after_part = sentence[transition_pos:]
                    
                    # 简化处理：转折后的情感更重要
                    if len(after_part) > len(before_part):
                        sentence_positive *= 0.7
                        sentence_negative *= 0.7
            
            positive_score += sentence_positive
            negative_score += sentence_negative
        
        return positive_score, negative_score
    
    def analyze_rating_impact(self, features):
        """分析评分数字对情感的影响"""
        rating_impact = 0.0
        if features['rating_numbers']:
            avg_rating = sum(features['rating_numbers']) / len(features['rating_numbers'])
            
            # 根据评分判断情感倾向
            if avg_rating >= 8.0:
                rating_impact = 1.5  # 高分，强烈积极
            elif avg_rating >= 7.0:
                rating_impact = 1.0  # 较高分，积极
            elif avg_rating >= 6.0:
                rating_impact = 0.5  # 中等分，轻微积极
            elif avg_rating >= 4.0:
                rating_impact = 0.0  # 中等分，中性
            elif avg_rating >= 3.0:
                rating_impact = -0.5 # 较低分，轻微消极
            else:
                rating_impact = -1.5 # 低分，强烈消极
        
        return rating_impact

    def analyze_sentiment(self, text):
        """增强的情感分析
        
        Returns:
            tuple: (sentiment, score, confidence)
            - sentiment: 'positive', 'negative', 'neutral', 'unknown'
            - score: 情感得分 (-1 到 1)
            - confidence: 置信度 (0 到 1)
        """
        if not text or len(text.strip()) == 0:
            return 'unknown', 0.0, 0.0
        
        # 清理文本
        clean_text = self.clean_text(text)
        if len(clean_text) < 2:
            return 'unknown', 0.0, 0.0
        
        # 提取增强特征
        features = self.extract_features(clean_text)
        
        # 分析词汇情感（使用增强算法）
        positive_score, negative_score = self.analyze_words(clean_text)
        
        # 分析评分数字影响
        rating_impact = self.analyze_rating_impact(features)
        
        # 综合所有特征得分
        total_positive = positive_score + features['emoji_positive'] * 0.8
        total_negative = negative_score + features['emoji_negative'] * 0.8
        
        # 应用评分数字影响
        if rating_impact > 0:
            total_positive += rating_impact
        elif rating_impact < 0:
            total_negative += abs(rating_impact)
        
        # 应用转折词影响
        if features['transition_impact'] < 0:
            # 转折词通常表示情感的转向，增加不确定性
            uncertainty_factor = abs(features['transition_impact'])
            total_positive *= (1 - uncertainty_factor * 0.2)
            total_negative *= (1 - uncertainty_factor * 0.2)
        
        # 标点符号的情感增强
        exclamation_boost = min(features['exclamation_count'] * 0.3, 1.0)
        if total_positive > total_negative:
            total_positive += exclamation_boost
        elif total_negative > total_positive:
            total_negative += exclamation_boost
        
        # 文本长度权重调整
        length_factor = min(1.0 + len(clean_text) / 200, 1.5)  # 长文本权重略高
        total_positive *= length_factor
        total_negative *= length_factor
        
        # 计算最终情感得分
        total_score = total_positive + total_negative
        
        if total_score == 0:
            sentiment = 'neutral'
            score = 0.0
            confidence = 0.2
        else:
            # 计算情感倾向
            sentiment_score = (total_positive - total_negative) / max(total_score, 1.0)
            
            # 动态阈值（基于置信度调整）
            base_threshold = 0.15
            strength = abs(sentiment_score)
            
            # 根据情感强度确定类别
            if sentiment_score > base_threshold:
                if strength > 0.6:
                    sentiment = 'positive'
                elif strength > 0.3:
                    sentiment = 'positive'
                else:
                    sentiment = 'positive' if strength > base_threshold else 'neutral'
            elif sentiment_score < -base_threshold:
                if strength > 0.6:
                    sentiment = 'negative'
                elif strength > 0.3:
                    sentiment = 'negative'
                else:
                    sentiment = 'negative' if strength > base_threshold else 'neutral'
            else:
                sentiment = 'neutral'
            
            # 限制得分范围
            score = max(-1.0, min(1.0, sentiment_score))
            
            # 增强的置信度计算
            # 基于多个因素：词汇密度、文本长度、特征丰富度
            word_density = total_score / max(len(clean_text.split()), 1)
            feature_richness = (
                len(features['rating_numbers']) * 0.2 +
                features['emoji_positive'] * 0.1 +
                features['emoji_negative'] * 0.1 +
                bool(features['exclamation_count']) * 0.1
            )
            
            confidence = min(1.0, word_density * 2 + feature_richness + strength)
            confidence = max(0.25, confidence)  # 最低置信度
            
            # 特殊情况调整
            if features['rating_numbers']:
                confidence += 0.15  # 有明确评分的评论置信度更高
            if features['transition_impact'] < -1.0:
                confidence *= 0.8  # 多个转折词降低置信度
        
        return sentiment, score, confidence

    def batch_analyze(self, texts):
        """批量分析情感"""
        results = []
        for text in texts:
            sentiment, score, confidence = self.analyze_sentiment(text)
            results.append({
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence
            })
        return results

    def get_sentiment_display(self, sentiment, score):
        """获取情感显示信息"""
        sentiment_info = {
            'positive': {'name': '积极', 'color': 'success', 'icon': 'emoji-smile'},
            'negative': {'name': '消极', 'color': 'danger', 'icon': 'emoji-frown'},
            'neutral': {'name': '中性', 'color': 'secondary', 'icon': 'emoji-neutral'},
            'unknown': {'name': '未知', 'color': 'light', 'icon': 'question-circle'}
        }
        
        info = sentiment_info.get(sentiment, sentiment_info['unknown'])
        info['score'] = score
        return info


# 全局情感分析器实例
sentiment_analyzer = SentimentAnalyzer()


def analyze_comment_sentiment(comment_text):
    """分析单条评论的情感"""
    return sentiment_analyzer.analyze_sentiment(comment_text)


def update_comment_sentiments():
    """更新所有评论的情感分析结果"""
    from app.models import Comment
    
    comments = Comment.objects.filter(sentiment='unknown')
    updated_count = 0
    
    for comment in comments:
        if comment.content and len(comment.content.strip()) > 0:
            sentiment, score, confidence = analyze_comment_sentiment(comment.content)
            comment.sentiment = sentiment
            comment.sentiment_score = score
            comment.save()
            updated_count += 1
    
    return updated_count


def test_sentiment_analysis():
    """测试情感分析准确性"""
    test_cases = [
        # 积极评论
        ("这部电影太棒了，演技很好，剧情精彩，9分推荐！", 'positive'),
        ("超级好看，值回票价，五星好评", 'positive'),
        ("导演功力深厚，制作精良，不愧是佳作", 'positive'),
        
        # 消极评论  
        ("演技太差了，剧情无聊，浪费时间，1分", 'negative'),
        ("看了半小时就想退票，太烂了", 'negative'),
        ("拖沓冗长，毫无看点，年度最差", 'negative'),
        
        # 转折句测试
        ("开头还不错，但是后面越来越无聊", 'negative'),
        ("虽然有些瑕疵，不过整体还是很精彩的", 'positive'),
        
        # 否定句测试
        ("演技不差，剧情不无聊", 'positive'),
        ("不是很好看，但也不算太差", 'neutral'),
        
        # 中性评论
        ("还可以吧，一般般的电影", 'neutral'),
        ("看完了，没什么特别的感觉", 'neutral'),
    ]
    
    analyzer = SentimentAnalyzer()
    correct_count = 0
    total_count = len(test_cases)
    
    print("=== 情感分析测试结果 ===")
    for text, expected in test_cases:
        sentiment, score, confidence = analyzer.analyze_sentiment(text)
        is_correct = sentiment == expected
        correct_count += is_correct
        
        print(f"文本: {text}")
        print(f"预期: {expected} | 实际: {sentiment} | 得分: {score:.3f} | 置信度: {confidence:.3f} | {'✓' if is_correct else '✗'}")
        print("-" * 50)
    
    accuracy = correct_count / total_count * 100
    print(f"准确率: {accuracy:.1f}% ({correct_count}/{total_count})")
    
    return accuracy