def from_DT_Scale_to_treble_bass(x):
    y = int(x)*14/100
    if len(str(y)) < 2:
        return "0" + str(y) 
    else:
        return int(round(y))
