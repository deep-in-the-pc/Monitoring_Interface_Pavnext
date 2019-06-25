def charToAscii(char):
    return str(chr(ord(char))).encode('ascii')

def stringToAscii(string):
    returnString = str()
    for i in string:
        returnString = returnString + charToAscii(i).decode('ascii')
    return returnString.encode('ascii')