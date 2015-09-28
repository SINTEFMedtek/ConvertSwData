import os

def readTagFiles(filePathIn):
    if not filePathIn[-4:] == ".ini":
        return None

    res = {}
    with open(filePathIn, 'r') as f:
        for line in f:
            splitLine = line.split()
            if len(splitLine) > 1:
                valueTemp = line.split('"')
                if len(valueTemp) < 2:
                    continue
                value = valueTemp[1]
                value = value.replace('"', '')  # remove " from string
                res[splitLine[0]] = value
    if not "Version" in res.keys():
        return None
    print res["Version"]
    if not float(float(res["Version"])) == 1.0:
        return None
    return res


def writeFcsv(filePathOut, tagData):
    buffer = '# Markups fiducial file version = 4.4' + os.linesep
    buffer +='# CoordinateSystem = 1' + os.linesep
    buffer += "# columns = id,x,y,z,ow,ox,oy,oz,vis,sel,lock,label,desc,associatedNodeID'" + os.linesep
    
        
    
    for val in tagData:
        name = val['Name'].split()[1]
        buffer +=  val['Name'].replace(" ","_") + "," + val['PositionGlobal'].replace(" ","_")  + ",0,0,0,1,1,1,0," +name +",," + os.linesep
    fcsv_file = open(filePathOut, 'w')
    fcsv_file.write(buffer)
    fcsv_file.close()
