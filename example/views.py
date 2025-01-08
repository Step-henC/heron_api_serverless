# example/views.py
# from datetime import datetime

# from django.http import HttpResponse

# def index(request):
#     now = datetime.now()
#     html = f'''
#     <html>
#         <body>
#             <h1>Hello from Vercel!</h1>
#             <p>The current time is { now }.</p>
#         </body>
#     </html>
#     '''
#     return HttpResponse(html)

from django.http import HttpResponse
import pandas as pd
import re
import math
import xlsxwriter
import io
from django.views.decorators.csrf import csrf_exempt
import json
# Create your views here.

def parseSialicAcidFromString(proteinNameString):
    if re.search('^SA[0-9]', proteinNameString):
        return re.split('^SA[0-9]', proteinNameString, 1)[1]
    return proteinNameString

def parseGalNacsFromString(proteinNameString): # receives str from parseSialicAcidFromString 
    if re.search('Gal[0-9]{1,}$', proteinNameString): # the result is SA1GalNac3Gal2 -> GalNac3
        saGalNac = re.split("Gal[0-9]{1,}$", proteinNameString)[0]
        galNac = re.sub('^SA[0-9]', "", saGalNac)
    return galNac

@csrf_exempt
def index(request):
  
  if request.method == 'POST':
      
      data = json.loads(request.body)
      # converting to string now, but may send data as a json string?
      jsonString = json.dumps(data)
      df = pd.read_json(io.StringIO(jsonString))
      
      
      # begin grouping proteins by galnacGal numbers
      listOfGalNacGals = df.to_dict('records')
      groupedSheetsByGalNacGal = {}
      groupedSheetsByGalNac = {}
      
      
      for row in listOfGalNacGals:
        dictForDataframe = {}
        proteinName = row["Protein Name"]

        dictForDataframe["Peptide"] = proteinName
        dictForDataframe["Replicate"] = row["Replicate Name"]
      
        if math.isnan(row["Total Area"]):
          
          dictForDataframe["Total Area"] = 0
     
        dictForDataframe["Total Area"] = row["Total Area"]
            
        parsedProteinName = parseSialicAcidFromString(proteinName)
        parsedGalNacName = parseGalNacsFromString(proteinName)

        # add to sheet. 
        if parsedProteinName in groupedSheetsByGalNacGal:
          groupedSheetsByGalNacGal[parsedProteinName] += [dictForDataframe]
        else: 
          groupedSheetsByGalNacGal[parsedProteinName] = []
          groupedSheetsByGalNacGal[parsedProteinName]  += [dictForDataframe]

        if parsedGalNacName in groupedSheetsByGalNac:
           groupedSheetsByGalNac[parsedGalNacName] += [dictForDataframe]
        else:
           groupedSheetsByGalNac[parsedGalNacName] = []
           groupedSheetsByGalNac[parsedGalNacName] += [dictForDataframe]
          
      buffer = io.BytesIO()  
      
      with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    #------------GalNacGal Sheets ------------------------
          for k, v in groupedSheetsByGalNacGal.items():
              dfRaw = pd.DataFrame(v)
              dfPivot = pd.pivot_table(dfRaw, index=["Peptide"], values="Total Area", columns=["Replicate"], aggfunc="sum", fill_value=0, margins=True, margins_name="Summed Total Area")
              max_rows = dfPivot.shape[0]
              max_cols = dfPivot.shape[1]

              # cannot "apply" to dfpivot cuz marings Sum column washes out percentages
              dfPercentages = pd.pivot_table(dfRaw, index=["Peptide"], values="Total Area", columns=["Replicate"], aggfunc="sum", fill_value=0).apply(lambda x: x*100/sum(x))

              dfAvgOfPercentages = dfPercentages.T.groupby(lambda x: re.split('_\\d$', x)[0]).mean().T
              dfAvgOfPercentagesRowStart = max_rows+max_rows+10
              avgTableColCount = dfAvgOfPercentages.shape[1]

              dfPivot.to_excel(writer, sheet_name=k)
              dfPercentages.to_excel(writer, sheet_name=k, startrow=max_rows+5, startcol=0)
              dfAvgOfPercentages.to_excel(writer, sheet_name=k, startrow=max_rows+max_rows+10)
             

              worksheet = writer.sheets[k]
              workbook = writer.book

              worksheet.write(max_rows+4, 0, "Percent Relative Abundance (area/total area for peaks considered * 100)")
              worksheet.write(max_rows+max_rows+9,0, "Replicate Average Percent Relative Abundance")

              colValIterator = 1
              for series_name, _ in dfAvgOfPercentages.items():
                  
                chart = workbook.add_chart({'type': 'pie'})

                chart.add_series({
                  "name": series_name,
                  "categories": [k, dfAvgOfPercentagesRowStart+1, 0, dfAvgOfPercentagesRowStart+max_rows-1, 0],
                  "values": [k, dfAvgOfPercentagesRowStart+1, colValIterator, dfAvgOfPercentagesRowStart+max_rows-1, colValIterator],
              })

                worksheet.insert_chart("H"+str(colValIterator+5), chart)
                colValIterator += 1
    #-------------GalNac Sheets-------------------------------
          for k, v in groupedSheetsByGalNac.items():
              dfRaw = pd.DataFrame(v)
              dfPivot = pd.pivot_table(dfRaw, index=["Peptide"], values="Total Area", columns=["Replicate"], aggfunc="sum", fill_value=0, margins=True, margins_name="Summed Total Area")
              max_rows = dfPivot.shape[0]
              max_cols = dfPivot.shape[1]

              # cannot "apply" to dfpivot cuz marings Sum column washes out percentages
              dfPercentages = pd.pivot_table(dfRaw, index=["Peptide"], values="Total Area", columns=["Replicate"], aggfunc="sum", fill_value=0).apply(lambda x: x*100/sum(x))

              dfAvgOfPercentages = dfPercentages.T.groupby(lambda x: re.split('_\\d$', x)[0]).mean().T
              dfAvgOfPercentagesRowStart = max_rows+max_rows+10
              avgTableColCount = dfAvgOfPercentages.shape[1]

              dfPivot.to_excel(writer, sheet_name=k)
              dfPercentages.to_excel(writer, sheet_name=k, startrow=max_rows+5, startcol=0)
              dfAvgOfPercentages.to_excel(writer, sheet_name=k, startrow=max_rows+max_rows+10)
             

              worksheet = writer.sheets[k]
              workbook = writer.book

              worksheet.write(max_rows+4, 0, "Percent Relative Abundance (area/total area for peaks considered * 100)")
              worksheet.write(max_rows+max_rows+9,0, "Replicate Average Percent Relative Abundance")

              colValIterator = 1
              for series_name, _ in dfAvgOfPercentages.items():
                  
                chart = workbook.add_chart({'type': 'bar'})

                chart.add_series({
                  "name": series_name,
                  "categories": [k, dfAvgOfPercentagesRowStart+1, 0, dfAvgOfPercentagesRowStart+max_rows-1, 0],
                  "values": [k, dfAvgOfPercentagesRowStart+1, colValIterator, dfAvgOfPercentagesRowStart+max_rows-1, colValIterator],
              })

                worksheet.insert_chart("H"+str(colValIterator+5), chart)
                colValIterator += 1
      writer.close()
      buffer.seek(0)
      filename = 'sample-sheets.xlsx'
      response = HttpResponse(
        buffer.getvalue(),
         content_type='application/vnd.openxmlformats-officedocument.spreedsheetml.sheet'
              )
      response['Content-Disposition'] = 'attachment; filename=%s' % filename
      return response
    
  else:
    return HttpResponse('Heron Data Copyright 2025')