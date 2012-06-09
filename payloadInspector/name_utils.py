

# Common functions for making file names. Should only be used from SubdetectorFactory. Use SubdetectorFactory from other modules.

def ecal_get_names(dbName, tag, since = '1', fileType = 'png', basedir = './'):
    """Return file name."""
    name = tag + '_' + str(since) + '.' + fileType
    return [name, ]
    
def strip_get_names(dbName, tag, since = '1', fileType = 'png', basedir = './', prefix = 'SiStrip'):
    newTags = []
    tagsWithoutPrefix = []
    tagName = tag.split("_", 1)[0]
    if fileType != "": 
        fileType = "." + fileType
    tagsWithoutPrefix.append(tagName.replace(prefix, "", 1))
    if tagsWithoutPrefix[0] == "Pedestals" or tagsWithoutPrefix[0] == "Pedestals":
        tagsWithoutPrefix[0] = "Pedestal"
    elif tagsWithoutPrefix[0] == "Noise" or tagsWithoutPrefix[0] == "Noises":
        tagsWithoutPrefix[0] = "Noise"
    elif tagsWithoutPrefix[0] == "Threshold" or tagsWithoutPrefix[0] == "ClusterThreshold":
        tagsWithoutPrefix = ["LowThreshold", "HighThreshold"]
    elif tagsWithoutPrefix[0][0:3] == "Bad" or tagsWithoutPrefix[0] == "DetVOff":
        tagsWithoutPrefix[0] = "Quality"
    for t in tagsWithoutPrefix:
        newTags.append(str(tag)+"_"+str(t)+ "TkMap_Run_"+str(since)+str(fileType))
    #newTags.append(str(tagWithoutPrefix)+ "TkMap_Run_"+str(since)+str(fileType))
    return newTags
    
def get_directory(dbName, tag = '', since = '1', fileType = 'png', basedir = './'):
    return os.path.join(basedir, get_formatted_db_name(dbName))