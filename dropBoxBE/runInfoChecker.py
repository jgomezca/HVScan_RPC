import os
import json

data = json.loads(open('runInfoFromLog.json','rb').read())
runInfoData = {}
emptyHltCount  = 0
emptyPromptCount  = 0
fileNameCount = 0
exportCount = 0
duplicateCount = 0
fromDuplicate = False
for filename in data:
    hlt = set()
    prompt = set()
    fromDuplicate = False
    for (i,t,value) in data[filename]:
        if i=='export':
            exportCount += 1
        if i=='duplicate':
            fromDuplicate = True
        if t=='hlt' or t=='express':
            hlt.add(value)
        if t=='prompt':
            prompt.add(value)
    
    if len(hlt)>1:
        print filename,hlt
    if len(prompt)>1:
        print filename,prompt
    if len(hlt)==0:
        hlt.add(1)
        emptyHltCount += 1
    if len(prompt)==0:
        prompt.add(1)
        emptyPromptCount += 1
    fileNameCount += 1
    runInfoData[filename] = (hlt.pop(),prompt.pop())
    if fromDuplicate:
        duplicateCount += 1

with open('runInfoFromLogForReplay.json','wb') as f:
    json.dump(runInfoData,f)
print 'Files: %d empty hlt: %d empty prompt: %d. From export: %d, from duplicate: %d.' %(fileNameCount,emptyHltCount,emptyPromptCount, exportCount, duplicateCount )
