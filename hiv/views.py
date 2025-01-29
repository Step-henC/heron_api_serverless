

from django.http import HttpResponse
import pandas as pd
import re
import math
import xlsxwriter
import io
from django.views.decorators.csrf import csrf_exempt
import json

def parseHexNac(str):
  if re.search("HexNAc", str) == None:
    return 0
  if re.search('HexNAc[0-9]$', str): 
    return int(str[-1]) #if hexnac num at end, return last num
  arr = re.split("HexNAc", str) #all should have HexNAc
  return int(arr[-1][0]) #return first char of last elem

def parseFucose(str): 
  if re.search("dHex", str):
    temp = re.split("dHex", str, 1)
    return int(temp[-1][0])
  else:
    return None
  
def parseHex(str): 
  if re.search("[^d]Hex[0-9]HexNAc", str):
    temp = re.split("[^d]Hex", str, 1)
    return int(temp[-1][0])
  else:
    return None
  
def parseSA(str): 
  if re.search("NeuAc", str):
    return int(str[-1]) #Pattern at end of string if it exist, followed by target num
  else:
    return None

@csrf_exempt
def transformHivData(request):
  
  if request.method == 'POST':
      data = json.loads(request.body)
      # converting to string now, but may send data as a json string?
      jsonString = json.dumps(data)
      df = pd.read_json(io.StringIO(jsonString))
      hivRecords = df.to_dict('records')
      clean_data = {}
      clean_data['HexNAc'] = []
      clean_data['Hex'] = []
      clean_data["Fucose"] = []
      clean_data['SA'] = []
      clean_data["Short Name"] = []
      clean_data["Contruct 4, N156/N160 peptide"] = []
      
      for row in hivRecords[1:]: #first row (index zero) is just column names from UI
        clean_data['HexNAc'] += [parseHexNac(row[0])]
        clean_data['Hex'] += [parseHex(row[0])]
        clean_data["Fucose"] += [parseFucose(row[0])]
        clean_data['SA'] += [parseSA(row[0])]
        clean_data["Short Name"] += [row[0]]
        clean_data["Contruct 4, N156/N160 peptide"] += [row[4]]
        
      buffer = io.BytesIO()  
      with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
          dfRaw = pd.DataFrame(clean_data)
          dfRaw.to_excel(writer, sheet_name="clean data")
          
      
      writer.close()
      buffer.seek(0)
      filename="hiv-sample.xlsx"
      response = HttpResponse(
        buffer.getvalue(),
         content_type='application/vnd.openxmlformats-officedocument.spreedsheetml.sheet'
              )
      response['Content-Disposition'] = 'attachment; filename=%s' % filename
          
      return response
  
  else:
    return HttpResponse("Heron Data Copyright 2025")