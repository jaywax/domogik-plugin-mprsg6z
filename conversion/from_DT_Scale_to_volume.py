def from_DT_Scale_to_volume(x):
    y = int(x)*38/100
    if len(str(y)) < 2:
        return "0" + str(y)
    else:
        return int(round(y))

