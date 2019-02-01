from bs4 import BeautifulSoup
import requests
import pandas as pd


page_link = 'https://developers.arcgis.com/rest/services-reference/projected-coordinate-systems.htm'

page_response = requests.get(page_link, timeout=5)
page_content = BeautifulSoup(page_response.content, "html.parser")

wkt_table = page_content.find_all("table")

rows = wkt_table[0].find_all('tr')

wkts = []
for row in rows:
    cells = row.findChildren('td')
    wkt = []
    for cell in cells:
        value = cell.string
        wkt.append(value)

    wkts.append(wkt)

wkts_df = pd.DataFrame(wkts)
wkts_df.to_csv('Z:\qaqc\wkts.csv', index=False)
print wkts_df

#wkts = [wkts[i].text for i in range(len(wkts))]


#wkts = []
#for i in range(0, 20):
#    wkt = page_content.find_all("tr")[i].text
#    print wkt
#    wkts.append(wkt)







