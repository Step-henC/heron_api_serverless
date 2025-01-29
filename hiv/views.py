

from django.http import HttpResponse
import pandas as pd
import re
import math
import xlsxwriter
import io
from django.views.decorators.csrf import csrf_exempt
import json

def parseHexNac(str):
  if re.match('HexNAc', str) == None:
    return str
  elif re.match('HexNAc[0-9]$', str):
    return int(str[-1])
  arr = re.split("HexNAc", str)
  return int(arr[len(arr) - 1][0]) #return first char of last elem

@csrf_exempt
def transformHivData(request):
  
  if request.method == 'POST':
      return HttpResponse('Not Yet Implemented')
      data = json.loads(request.body)
      # converting to string now, but may send data as a json string?
      jsonString = json.dumps(data)
      df = pd.read_json(io.StringIO(jsonString))
      hivRecords = df.to_dict('records')
      clean_data = []
      
      for row in hivRecords[1:]:
        dictForDataFrame = {}
        dictForDataFrame['HexNac'] = parseHexNac(row[0])
        hexArr = re.split("[^d]Hex", row[0])
        dictForDataFrame['Hex'] = hexArr[len(hexArr)-1][0]
        fucArr = re.split("[d]Hex", row[0])
        dictForDataFrame["Fucose"] = fucArr[len(fucArr)-1][0]
        sa_arr = re.split("NeuAc", row[0])
        dictForDataFrame['SA'] = sa_arr[len(sa_arr) -1][0]
        dictForDataFrame["Short Name"] = row[0]
        dictForDataFrame["Contruct 4, N156/N160 peptide"] = row[4]
        clean_data += [dictForDataFrame]
        
      buffer = io.BytesIO()  
      with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for v in clean_data:
          print(v)
          dfRaw = pd.DataFrame(v)
          dfPivot = pd.pivot_table(dfRaw, index=["Short Name"], values=["Fucose"], columns=["Hex"])
          dfPivot.to_excel(writer, sheet_name="clean data")
          
      
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