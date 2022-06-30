def get_rating_value(rating):
    data=0
    if rating > 0 and rating <= 0.9:
        data = 1
    elif rating > 2 and rating <= 2.9:
        data = 2
    elif rating > 3 and rating <= 3.9:
        data = 3
    elif rating > 4 and rating <= 4.9:
        data = 4
    elif rating == 0:
        data = 0
    else:
        data = 5
    return data