import requests
import json
import os
import pandas as pd
import time
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime

# Written by Andy Lien (@andy922200)
# Under the MIT license

def cls():
    # clear terminal
    os.system('cls' if os.name == 'nt' else 'clear')

class LouisVuittonAPI(object):
    def __init__(self, regions, exportMode):
        cls()
        self.now = datetime.utcnow()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36'
        }
        self.region_to_lang = {
            'UK': 'eng-gb',
            'AU': 'eng-au',
            'US': 'eng-us',
            'HK': 'eng-hk',
            'FR': 'fra-fr',
            'KR': 'kor-kr',
            'JP': 'jpn-jp',
            'TW': 'zht-tw'
        }
        self.export_mode = ''
        self.result = {
            'items': [],
            'lv_regions': [],
            'fetch_time': ''
        }

        if exportMode.upper() == 'XLSX':
            self.export_mode = 'XLSX'
        elif exportMode.upper() == 'JSON':
            self.export_mode  = 'JSON'
        else:
            raise ValueError('Invalid Export Mode')

        try:
            for region in regions:  
                self.result['lv_regions'].append({
                    'lang': self.region_to_lang[region.upper()],
                    'region': region.upper()
                })
        except:
            print("Invalid region, correct your spelling or add it.")
            raise ValueError('Invalid region')

    def get_products(self, skuNumbers):
        self.result['fetch_time'] = self.now.isoformat(timespec="seconds")
        for lvRegion in self.result['lv_regions']:
            for skuId in skuNumbers :
                tempResult = self.fetch_product_info(skuId.upper(), lvRegion)

                time.sleep(0.5)
                if tempResult is not None :
                    self.result['items'].append(tempResult)
            time.sleep(2)

        if self.export_mode == 'JSON':
            self.exportJson()
        
        if self.export_mode == 'XLSX':
            self.exportXlsx()
    
    def fetch_product_info(self, sku, lvRegion):
        """
        Prints product information.

        Args:
            sku: Louis Vuitton product SKU.
            lvRegion: Louis Vuitton Website Region
        """

        sku = sku.upper()
        print("=" * 60)
        print(f"Getting product info for {sku}...")
        print(f"Region: {lvRegion['region']}")
        print("=" * 60)

        sku_simple_info_url= f"https://api.louisvuitton.com/api/{lvRegion['lang']}/catalog/sku/{sku}/persodetails"
        sku_simple_info_url_text = requests.get(sku_simple_info_url, headers = self.headers).text
        sku_simple_info = json.loads(sku_simple_info_url_text)

        if  sku_simple_info.get('errors') and len(sku_simple_info['errors']) > 0:
            print('No Data')
            return None

        if  sku_simple_info['productId']:
            product_info_url = f"https://api.louisvuitton.com/api/{lvRegion['lang']}/catalog/product/{sku_simple_info['productId']}"
            product_info_url_text = requests.get(product_info_url, headers = self.headers).text
            product_info = json.loads(product_info_url_text)
        
            if  product_info:
                result = {}

                for prodKey, prodValue in product_info.items():
                    if (prodKey == 'name'):
                        result[prodKey] = prodValue

                    if prodKey == 'model':
                        targetValue = list(filter(lambda p: p['identifier'] == sku, prodValue))
                        if len(targetValue)>0:             
                            result['sku'] = targetValue[0]['identifier']
                            result['price'] = targetValue[0]['offers']['priceSpecification']['price']
                            result['currency'] = 'USD' if lvRegion['region'] == 'US' else targetValue[0]['offers']['priceSpecification']['priceCurrency']
                            result['description'] = BeautifulSoup(targetValue[0]['disambiguatingDescription'], "lxml").text
                            result['image'] = [ item['contentUrl'] for item in targetValue[0]['image']]

                            if 'color' in targetValue[0]:
                                result['color'] = targetValue[0]['color']
                            else:
                                result['color'] = ''

                result['fetchTime'] = f"{self.result['fetch_time']}Z"
                result['productId'] = sku_simple_info['productId']
                result['region'] = lvRegion['region']

                print("Product Info:")
                print(f"SKU: {result['sku']}")
                print(f"PID: {result['productId']}")
                print(f"Name: {result['name']}")
                print(f"Price: {result['price']}")
                print(f"Currency: {result['currency']}")
                print(f"Description: {result['description']}")
                return result

    def exportXlsx(self):
        result_df = {}
        for item in self.result['items']:
            for objKey, objValue in item.items():
                if objKey in result_df:
                    result_df[objKey] = [*result_df[objKey], objValue]
                else:
                    result_df[objKey] = [objValue]
        df = pd.DataFrame(result_df)
        df = df[['sku','productId', 'name','price','currency','color','region','fetchTime','description']]
        df.index = np.arange(1, len(df)+1)
        df.to_excel(f'./{self.result["fetch_time"].replace(":","-")}Z.xlsx')
    
    def exportJson(self):
        with open(f'./{self.result["fetch_time"].replace(":","-")}Z.json', "w", encoding="utf8") as outfile:
            json.dump(self.result, outfile, ensure_ascii=False)

# if the file is imported, it will not be executed once.
if __name__ == '__main__':
    cls()
    print("Louis Vuitton Crawler by Andy Lien (@andy922200)")
    print("=" * 60)

    regionInputs = input("Region Options ( UK,AU,US,FR,HK,KR,JP,TW ) ? Please use \",\" to separate.: ")
    skuNumberInputs = input("SKU Numbers? Please use \",\" to separate. :")
    exportMode= input("Export Format ( JSON, XLSX ) :")

    regions = [regionInput.replace(' ', '') for regionInput in regionInputs.split(',')]
    skuNumbers = [skuNumberInput.replace(' ', '') for skuNumberInput in skuNumberInputs.split(',')]

    lv = LouisVuittonAPI(regions, exportMode)
    lv.get_products(skuNumbers)
