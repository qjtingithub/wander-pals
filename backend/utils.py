from models import User, Itinerary, Recommendation

def find_team(user):
    # 获取用户的旅游意向
    itinerary = Itinerary.query.filter_by(user_id=user.id).first()
    
    if not itinerary:
        return []
    
    # 提取用户的行程需求
    destination = itinerary.destination.lower()
    time = itinerary.time
    price = itinerary.price
    companion_requirements = [req.strip().lower() for req in itinerary.companion_requirements.split(',')]
    
    # 权重分配
    weights = {
        'destination': 0.4,
        'time': 0.3,
        'price': 0.2,
        'companion_requirements': 0.1
    }
    
    # 获取所有其他用户
    potential_companions = User.query.filter(User.id != user.id).all()
    
    recommendations = []
    
    for companion in potential_companions:
        companion_itinerary = Itinerary.query.filter_by(user_id=companion.id).first()
        if not companion_itinerary:
            continue
        
        # 计算匹配评分
        score = 0
        
        # 景点评分
        if destination in companion_itinerary.destination.lower():
            score += weights['destination']
        
        # 时间评分
        if time == companion_itinerary.time:
            score += weights['time']
        
        # 价格评分
        if price == companion_itinerary.price:
            score += weights['price']
        
        # 同伴要求评分
        companion_interests = companion.interests.lower()
        match_count = sum(1 for req in companion_requirements if req in companion_interests)
        if companion_requirements:
            companion_score = (match_count / len(companion_requirements)) * weights['companion_requirements']
            score += companion_score
        
        # 保存推荐结果
        recommendations.append((companion, score))
    
    # 按评分排序
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    return recommendations

def calculate_match_score(current_user, user_to_match, team):
    # 计算用户与当前用户所建团队的匹配度
    score = 0

    # 权重分配
    weights = {
        'age': 0.1,
        'budget': 0.5,
        'interests': 0.2,
        'requirements': 0.1,
        'location': 0.1
    }

    # 年龄差距
    score_age =  1 - (abs(user_to_match.age - current_user.age) / 120)
    # 价格要求
    score_bugdet = (int(user_to_match.budget) >= int(team.price))
    # 旅行兴趣
    score_interest = (team.destination.lower() in user_to_match.interests.lower())
    # 同伴要求
    score_requirements = (user_to_match.interests.lower() in team.companion_requirements.lower())
    # 位置匹配
    score_location = (current_user.location.lower() in user_to_match.location.lower())

    score = weights['age'] * score_age + weights['budget'] * score_bugdet + weights['interests'] * score_interest + weights['requirements'] * score_requirements + weights['location'] * score_location

    return score * 100


def recommend_itinerary(user):
    # Placeholder logic for recommending itineraries
    itineraries = Itinerary.query.all()
    return itineraries
