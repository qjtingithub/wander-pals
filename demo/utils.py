from models import User, Itinerary, Recommendation

def find_team(user):
    # 获取用户的旅游意向
    itinerary = Itinerary.query.filter_by(user_id=user.id).first()
    
    if not itinerary:
        return []
    
    # 根据用户的队友要求筛选其他用户
    requirements = itinerary.companion_requirements.split(',')
    potential_companions = User.query.filter(User.id != user.id).all()
    
    recommendations = []
    for companion in potential_companions:
        if all(req in companion.interests for req in requirements):
            recommendations.append(companion)
    
    return recommendations

def recommend_itinerary(user):
    # Placeholder logic for recommending itineraries
    itineraries = Itinerary.query.all()
    return itineraries
