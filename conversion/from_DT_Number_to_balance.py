def from_DT_Number_to_balance(x):
    y = int(x)+10
    if len(str(y)) < 2:
        return "0" + str(y) 
    else:
        return int(y)
