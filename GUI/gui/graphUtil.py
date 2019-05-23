def dataConverter(slave, sensorid, dataid):
    adcBit, volt, sensorName = headerDecoder(slave['microprocessor'], slave['sensors'][sensorid]['function'])

    rstval =  slave['sensors'][sensorid]["restval"]
    data = slave['sensors'][sensorid]["entries"][dataid]["data"]
    processedR = None
    processedNR = None
    #time = slave['sensors'][sensorid]["entries"][dataid]["time"]
    #processedTime = [i for i in range(time, time+len(data))]
    #TODO add remaining convertions
    if(sensorName == "dlv"):
        processedR = list(map(lambda x: ((x-rstval)/(2**adcBit) * 300), data))
        processedNR = list(map(lambda x: ((x)/(2**adcBit) * 300), data))
    elif (sensorName == "dlh"):
        processedR = list(map(lambda x: ((x-rstval)/(2**adcBit) * 300), data))
        processedNR = list(map(lambda x: ((x)/(2**adcBit) * 300), data))
    elif (sensorName == "acx"):
        processedNR  =list(map(lambda x: (((x*3.3)/(2**adcBit)-1.65)/0.0065), data))
    elif (sensorName == "acy"):
        processedNR  =list(map(lambda x: (((x*3.3)/(2**adcBit)-1.65)/0.0065), data))
    elif (sensorName == "acz"):
        processedNR  =list(map(lambda x: (((x*3.3)/(2**adcBit)-1.65)/0.0065), data))
    elif (sensorName == "bie"):
        None
    elif (sensorName == "enl"):
        None
    elif (sensorName == "hum"):
        None
    elif (sensorName == "lum"):
        None
    elif (sensorName == "ten"):
        None
    elif (sensorName == "cor"):
        None
    elif (sensorName == "rpu"):
        None
    elif (sensorName == "rha"):
        None
    elif (sensorName == "tof"):
        None
    elif (sensorName == "tem"):
        Vsense = lambda x: (x*3.3)/(2**adcBit)
        V25 = 1.43
        Avg_slope = 0.0043
        temp = lambda x: (V25-Vsense(x))/Avg_slope + 25
        processedNR = list(map(lambda x: temp(x), data))
    elif (sensorName == "tpt"):
        vs = 5.01
        r = 62.1
        r1 = 986
        r2 = 989
        r3 = 986
        vdiff = lambda x: (x*3.3)/(2**adcBit) / (4 + 60 / r)
        res = lambda x: (r1 * vs + (r1 + r2) * (vdiff(x))) / (r2 * vs - (r1 + r2) * (vdiff(x))) * r3
        temp = lambda x: 0.000012218 * (res(x) ** 2) + 0.2294 * res(x) - 241.3

        processedNR = list(map(lambda x: temp(x), data))

    return((processedR, processedNR))#, processedTime)

def headerDecoder(uC, function):
    if(uC == 0 or uC == 1):
        adcBit = 10
        volt = 5
    elif(uC == 2 or uC == 3):
        adcBit = 12
        volt = 3.3
    if(function == 0):
        sensorName = "dlv"
    elif (function == 1):
        sensorName = "dlh"
    elif (function == 2):
        sensorName = "acx"
    elif (function == 3):
        sensorName = "acy"
    elif (function == 4):
        sensorName = "acz"
    elif (function == 5):
        sensorName = "bie"
    elif (function == 6):
        sensorName = "enl"
    elif (function == 7):
        sensorName = "tem"
    elif (function == 8):
        sensorName = "hum"
    elif (function == 9):
        sensorName = "lum"
    elif (function == 10):
        sensorName = "ten"
    elif (function == 11):
        sensorName = "cor"
    elif (function == 12):
        sensorName = "rpu"
    elif (function == 13):
        sensorName = "rha"
    elif (function == 14):
        sensorName = "tof"
    elif (function == 15):
        sensorName = "tpt"
    return adcBit, volt, sensorName
