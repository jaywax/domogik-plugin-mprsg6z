def from_DT_Scaling_to_balance(x):
    y = int(x)*20/100
    if len(str(y)) < 2:
        return "0" + str(y)
    else:
        return int(round(y))

