import os
import random

import pytest

#============================ defines ===============================

FILENAME    = 'temp_test_file.sol'
EXAMPLE_MAC = [0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08]

#============================ fixtures ==============================

def removeFileFunc():
    os.remove(FILENAME)

@pytest.fixture(scope='function')
def removeFile(request):
    #request.addfinalizer(removeFileFunc)
    try:
        os.remove(FILENAME)
    except WindowsError:
        # if file does not exist. NOT an error.
        pass

EXPECTEDRANGE = [
    (
         100, # startTimestamp
         300, # endTimestamp
         100, # idxMin
         301, # idxMax
    ),
    (
          -5, # startTimestamp
         300, # endTimestamp
           0, # idxMin
         301, # idxMax
    ),
    (
         100, # startTimestamp
        1100, # endTimestamp
         100, # idxMin
        1000, # idxMax
    ),
    (
          -5, # startTimestamp
        1100, # endTimestamp
           0, # idxMin
        1000, # idxMax
    ),
    (
        -500, # startTimestamp
        -100, # endTimestamp
           0, # idxMin
           0, # idxMax
    ),
    (
        1100, # startTimestamp
        1500, # endTimestamp
           0, # idxMin
           0, # idxMax
    ),
]

@pytest.fixture(params=EXPECTEDRANGE)
def expectedRange(request):
    return request.param

#============================ helpers ===============================

def getRandomObjects(num,startTs=0):
    returnVal = []
    for i in range(num):
        returnVal += [
            {
                'mac':       EXAMPLE_MAC,
                'timestamp': i+startTs,
                'type':      random.randint(0x00,0xff),
                'value':     [random.randint(0x00,0xff) for _ in range(random.randint(0,25))],
            }
        ]
    return returnVal

#============================ tests =================================

def test_dump_load(removeFile):
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump = getRandomObjects(1000)
    
    # dump
    sol.dumpToFile(dictsToDump,FILENAME)
    
    # load
    dictsLoaded = sol.loadFromFile(FILENAME)
    
    # compare
    assert dictsLoaded==dictsToDump

def test_dump_corrupt_load(removeFile):
    
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump1 = getRandomObjects(500)
    dictsToDump2 = getRandomObjects(500)
    
    # write first set of valid data
    sol.dumpToFile(dictsToDump1,FILENAME)
    # write HDLC frame with corrupt CRC
    with open(FILENAME,'ab') as f:
        bin = ''.join([chr(b) for b in [0x7E,0x10,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x00,0x00,0x00,0x00,0x75,0x94,0xE8,0x0B,0x6B,0xAE,0xE1,0x19,0x54,0x74,0xF3,0x00,0x00,0x7E]])
        f.write(bin) 
    # write some garbage
    with open(FILENAME,'ab') as f:
        f.write("############################## garbage ##############################")
    # write second set of valid data
    sol.dumpToFile(dictsToDump2,FILENAME)
    
    # load
    dictsLoaded = sol.loadFromFile(FILENAME)
    
    # compare
    assert dictsLoaded==dictsToDump1+dictsToDump2

def test_retrieve_range(removeFile,expectedRange):
    
    (startTimestamp,endTimestamp,idxMin,idxMax) = expectedRange
    
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump = getRandomObjects(1000)
    
    # dump
    sol.dumpToFile(dictsToDump,FILENAME)
    
    # load
    dictsLoaded = sol.loadFromFile(
        FILENAME,
        startTimestamp=100,
        endTimestamp=1900
    )
    
    # compare
    assert dictsLoaded==dictsToDump[100:]

def test_retrieve_range_corrupt_beginning(removeFile):
    
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump = getRandomObjects(1000)
    
    # dump
    with open(FILENAME,'ab') as f:
        f.write("garbage")
    sol.dumpToFile(dictsToDump,FILENAME)
    
    # load
    dictsLoaded = sol.loadFromFile(
        FILENAME,
        startTimestamp=100,
        endTimestamp=800
    )
    
    # compare
    assert dictsLoaded==dictsToDump[100:801]

def test_retrieve_range_corrupt_middle(removeFile):
    
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump1 = getRandomObjects(500)
    dictsToDump2 = getRandomObjects(500,startTs=500)
    
    # dump
    sol.dumpToFile(dictsToDump1,FILENAME)
    with open(FILENAME,'ab') as f:
        f.write("garbage")
    sol.dumpToFile(dictsToDump2,FILENAME)
    
    # load
    dictsLoaded = sol.loadFromFile(
        FILENAME,
        startTimestamp=100,
        endTimestamp=800
    )
    
    # compare
    assert dictsLoaded==(dictsToDump1+dictsToDump2)[100:801]

def test_retrieve_range_corrupt_end(removeFile):
    
    import Sol
    sol = Sol.Sol()
    
    # prepare dicts to dump
    dictsToDump = getRandomObjects(1000)
    
    # dump
    sol.dumpToFile(dictsToDump,FILENAME)
    with open(FILENAME,'ab') as f:
        f.write("garbage")
    
    # load
    dictsLoaded = sol.loadFromFile(
        FILENAME,
        startTimestamp=100,
        endTimestamp=800
    )
    
    # compare
    assert dictsLoaded==dictsToDump[100:801]

def test_retrieve_range_corrupt_all(removeFile):
    
    import Sol
    sol = Sol.Sol()
    
    # dump
    with open(FILENAME,'ab') as f:
        for _ in range(100):
            f.write("garbage")
    
    # load
    dictsLoaded = sol.loadFromFile(
        FILENAME,
        startTimestamp=100,
        endTimestamp=800
    )
    
    # compare
    assert dictsLoaded==[]