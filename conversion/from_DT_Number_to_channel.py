def from_DT_Number_to_channel(x):
    y = int(x)
    if len(str(y)) < 2:
        return "0" + str(y) 
    else:
        return int(y)
