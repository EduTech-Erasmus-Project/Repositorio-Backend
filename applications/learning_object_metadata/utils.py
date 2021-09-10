def get_rating_value(rating):
    data=0
    if rating > 0 and rating <= 0.4:
        data = 1
    elif rating > 0.4 and rating <= 0.8:
        data = 2
    elif rating > 0.8 and rating <= 1.2:
        data = 3
    elif rating > 1.2 and rating <= 1.7:
        data = 4
    elif rating == 0:
        data = 0
    else:
        data = 5
    return data