from werkzeug import secure_filename
import os
import glob
import csv
import json
import datetime
from operator import itemgetter
import re
import base64
from graph_data import *

UPLOAD_FOLDER ='data'
ALLOWED_EXTENSIONS = set(['csv'])

#file title config (also allows for capitalised version)
edgeFileName = "matrix"
nodeFileName = "bank"

#in file reading configuration is found in graph_data.py

def gettimestamp(f):
    thestring = f
    timeformat = re.compile("20\d\d\d\d")
    result = timeformat.search(thestring)
    if result:
        return (result.string[result.start():result.end()])

def cleaned_input(file):
    try:
        csv_input = csv.reader(file,delimiter='|')
        data=[]
        for idx,row in enumerate(csv_input):
                        for item in row:
                            item.replace('"','')
                        cleanedRow= row[0].split(';')
                        if idx == 0:
                            keyArray = cleanedRow
                        else:
                            valueArray = cleanedRow
                            dictRow = {}
                            for idx1,value in enumerate(valueArray):
                                dictRow[keyArray[idx1]] = value
                            #add_date(dictRow,edgeDates)
                            data.append(dictRow)
    except TypeError:
        flash('input not valid for file ' + file.filename)
        return []
    return data

def upload_file():

    UPLOAD_FOLDER ='data' 
    allFiles = os.listdir(UPLOAD_FOLDER)
    print(allFiles)
    #1) filter by edges and nodes
    edgeFiles = [f for f in allFiles if edgeFileName in f or edgeFileName.capitalize() in f]
    nodeFiles = [f for f in allFiles if nodeFileName in f or nodeFileName.capitalize() in f]
    print("accepted files")
    for f in nodeFiles:
        print(f)
    for f in edgeFiles:
        print(f)

    if edgeFiles == [] or nodeFiles == []:
        flash('Failed to read in files')
        return

    #2) get dates
    edgeFileDates = [gettimestamp(f) for f in edgeFiles]
    nodeFileDates = [gettimestamp(f) for f in nodeFiles]       
    
    #3) read in
    edges=[]
    nodes=[]
    keys=[]
    for idx, f in enumerate(edgeFiles):
        #check secure file and get full path
        filepath = os.path.join(UPLOAD_FOLDER, f)
  
        #save content in edges and nodes 
        with open(filepath) as file:
            newEdges = cleaned_input(file)
            if newEdges == []: 
                return 
            for row in newEdges:
                add_date(row,edgeFileDates[idx])
            edges = edges + newEdges
   
    for idx, f in enumerate(nodeFiles):
        #check secure file and get full path
        filepath = os.path.join(UPLOAD_FOLDER, f)

        with open(filepath) as file:
            newNodes = cleaned_input(file)
            if newNodes == []: 
                return
            for row in newNodes:
                add_date(row,nodeFileDates[idx])
            nodes = nodes + newNodes
            
        #save categories in keys 
        with open(filepath) as file:
                reader = csv.DictReader(file,delimiter=';')
                #if first file read in keys, for following files check the keys are right 
                if idx == 0:
                    keys = reader.fieldnames

    #add date categories to keys
    keys.append('date')
    keys.append('dateID')
    #check whether there is a node color provided
    customNodeColor = False
    if colorKey in keys: 
        customNodeColor = True

    #get the categories for node values and add no value (for default setting)
    categoryKeys=set_categories(nodes,keys)
    categoryKeys.append('no value')
   
    #put together array of dictionaries
    edges=transform_edges(edges)
    nodes=transform_nodes(nodes,keys)

    if edges == [] or nodes == []:
        return

    #get all dates
    unsortedDates=[]
    unique=[]
    for node in nodes:
        if node['dateID'] not in unique:
            unsortedDates.append({'date': node['date'], 'dateID': node['dateID']})
        unique.append(node['dateID'])
    dates = sorted(unsortedDates, key=itemgetter('dateID')) 

    #get all sectors
    sectors=[]
    unique=[]
    for node in nodes:
        if node['sector'] not in unique:
            sectors.append({'sector': node['sector']})
        unique.append(node['sector'])
    sectors.append({'sector': 'all'})

    #get all banks
    banks=[]
    unique=[]
    for node in nodes:
        if node['id'] not in unique:
            banks.append({'id': node['id']})
        unique.append(node['id'])

    #adding trend information to edges
    trend_edges(edges,dates)
    #package output as json files

    filename = 'edges.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(edges,file)

    filename = 'nodes.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(nodes,file)

    filename = 'dates.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(dates,file)

    filename = 'sectors.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(sectors,file)

    filename = 'banks.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(sectors,file)
    
    filename = 'categoryKeys.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(categoryKeys,file)

    filename = 'customNodeColor.json'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open (filepath,'w') as file:
        json.dump(customNodeColor,file)
  
    return

if __name__ == '__main__':
   upload_file()