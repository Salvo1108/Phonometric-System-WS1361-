import usb.core


ranges = ["30-80", "40-90", "50-100", "60-110", "70-120", "80-130", "30-130"]
speeds = ["fast", "slow"]
weights = ["A", "C"]
maxModes = ["instant", "max"]

#Funzione di connessione
def connect():
    dev = usb.core.find(idVendor=0x16c0, idProduct=0x5dc) #usb.core.find funzione che indentifica il dispositivo collegato
    assert dev is not None  #Se si riesce a indentificare il dispositivo si stampano le info
    print(dev)
    return dev

#Lettura richiesta
def readBRequest(dev, bRequest):
    ret = dev.ctrl_transfer(0xC0, bRequest, 0, 10, 200)
    print(ret),
    for elem in ret:
        print(format(elem, '#010b')),
    print
    
#Lettura dei Set
def readMode(dev):
    ret = dev.ctrl_transfer(0xC0, 2, 0, 10, 200)
    #print(ret)
    #print(format(ret[0], '#010b'))

    rangeN = (ret[0]&7) # bits 1,2,3 in ret[0] return rangeN from 0 to 6
    weightN = (ret[0]&8)>>3 # bit 3 in ret[0] returns weight
    speedN = (ret[0]&16)>>4 # bit 4 in ret[0] returns speed
    maxModeN = (ret[0]&32)>>5 # bit 5 in ret[0] returns maxMode

    return(ranges[rangeN], weights[weightN],
           speeds[speedN], maxModes[maxModeN])
#Set
def setMode(dev, range="30-80", speed="fast", weight="A", maxMode="instant"):
    rangeN = ranges[0:4].index(range)
    # Per il rangeN, l'impostazione tramite USB supporta solo 2 bit di range,
    # sebbene 7 valori (da 0 a 6) possano essere impostati con i pulsanti sull'unità.
    speedN = speeds.index(speed)
    weightN = weights.index(weight)
    maxModeN = maxModes.index(maxMode)

    print("setMode: range:%s weight:%s speed:%s maxMode:%s" %
          (range, weight, speed, maxMode))
    #wvalue = rangeN | weightN<<3 | speedN<<4 | maxModeN<<5
    wvalue = (rangeN&3) | (weightN&1)<<3 | (speedN&1)<<4 | (maxModeN&1)<<5
    # Function of bits 6 and 7 is unknown (nothing?)

    dev.ctrl_transfer(0xC0, 3, wvalue, 0, 200)
    
peak = 0
#Lettura Livello di Pressione Sonora
def readSPL(dev):
    global peak

    ret = dev.ctrl_transfer(0xC0, 4, 0, 10, 200) # wvalue (3rd arg) is ignored
    #print(ret)
    #print(format(ret[1], '#010b'))

    rangeN = (ret[1]&28)>>2 # bits 2,3,4 in ret[1] return rangeN from 0 to 6
    weightN = (ret[1]&32)>>5 # bit 5 in ret[1] return weightN
    speedN = (ret[1]&64)>>6 # bit 6 in ret[1] return speedN
    # bit 7 seems to alternate every 1 second?

    dB = (ret[0] + ((ret[1] & 3) * 256)) * 0.1 + 30
    if dB > peak:
        peak = dB
    return(dB, ranges[rangeN], weights[weightN], speeds[speedN])


if __name__ == "__main__":
    import datetime
    import time
    
    file = open("rilevazione.txt","w")

    # connect to WS1381 over USB
    dev = connect()

    # set default modes: "A" weighting, "fast"
    setMode(dev)

    millis = int(round(time.time() * 1000))
    millis1=int(round(time.time() * 1000 +36000000 ))#stampa 1 rilevazione per secondo per 10 ore.
    while millis<millis1:
        millis = int(round(time.time() * 1000))
        now = datetime.datetime.now()

        dB, range, weight, speed = readSPL(dev)
        file.write(now.strftime('%Y-%m-%d,%H:%M:%S'))
        file.write("-")
        file.write("DB "+ '{0:.2f}'.format(dB))
        file.write("-")
        file.write("Range "+ str(range))
        file.write("-")
        file.write("Weight "+ str(weight))
        file.write("-")
        file.write("Speed "+ str(speed))
        file.write("\n")
            
        print("%.2f,%s,%s,%s"
                % (dB, weight, speed, now.strftime('%Y,%m,%d,%H,%M,%S')))

        time.sleep(1)
    file.close()