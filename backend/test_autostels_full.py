#!/usr/bin/env python3
import requests
import base64
import xml.etree.ElementTree as ET
import sys

login_b64 = base64.b64encode(b'car.workshop72@mail.ru').decode()
password_b64 = base64.b64encode(b'Qq23321q').decode()

print("="*70, flush=True)
print("FULL TEST: Step1 -> Step2 with SessionGUID if available", flush=True)
print("="*70, flush=True)

# ===== STEP 1 =====
print("\n[STEP 1] Searching for article SP-1004", flush=True)

xml1 = f'''<root>
   <SessionInfo ParentID="39151" UserLogin="{login_b64}" UserPass="{password_b64}" />
   <Search>
      <Key>SP-1004</Key>
   </Search>
</root>'''

soap1 = f'''<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
<soapenv:Body>
<tem:SearchOfferStep1>
<tem:SearchParametersXml><![CDATA[{xml1}]]></tem:SearchParametersXml>
</tem:SearchOfferStep1>
</soapenv:Body>
</soapenv:Envelope>'''

r1 = requests.post(
    'https://services.allautoparts.ru/WebService2/SearchService.svc',
    data=soap1.encode('utf-8'),
    headers={
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferStep1'
    },
    timeout=10
)

print(f"Step1 HTTP Status: {r1.status_code}", flush=True)

root1 = ET.fromstring(r1.text)
res1 = root1.find('.//{http://tempuri.org/}SearchOfferStep1Result')

session_guid = None
product_id = None

if res1 is not None:
    # Парсим результат как текст или прямой XML
    if res1.text:
        result_root = ET.fromstring(res1.text)
    else:
        result_root = res1
    
    # Ищем SessionGUID
    session_guid = result_root.findtext('.//SessionGUID')
    product_id = result_root.findtext('.//ProductID')
    
    print(f"SessionGUID found: {session_guid is not None} ({session_guid[:30] if session_guid else 'None'}...)", flush=True)
    print(f"ProductID found: {product_id}", flush=True)

if not product_id:
    print("❌ No ProductID found in Step1, cannot proceed", flush=True)
    sys.exit(1)

# ===== STEP 2 =====
print(f"\n[STEP 2] Getting offers for ProductID={product_id}", flush=True)

# Используем SessionGUID если есть, иначе UserLogin/UserPass
if session_guid:
    print(f"Using SessionGUID for authentication", flush=True)
    session_info = f'<SessionInfo ParentID="39151" SessionGUID="{session_guid}" />'
else:
    print(f"Using UserLogin/UserPass for authentication", flush=True)
    session_info = f'<SessionInfo ParentID="39151" UserLogin="{login_b64}" UserPass="{password_b64}" />'

xml2 = f'''<root>
   {session_info}
   <Search>
      <ProductID>{product_id}</ProductID>
      <StocksOnly>0</StocksOnly>
   </Search>
</root>'''

soap2 = f'''<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
<soapenv:Body>
<tem:SearchOfferStep2>
<tem:SearchParametersXml><![CDATA[{xml2}]]></tem:SearchParametersXml>
</tem:SearchOfferStep2>
</soapenv:Body>
</soapenv:Envelope>'''

r2 = requests.post(
    'https://services.allautoparts.ru/WebService2/SearchService.svc',
    data=soap2.encode('utf-8'),
    headers={
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferStep2'
    },
    timeout=10
)

print(f"Step2 HTTP Status: {r2.status_code}", flush=True)

root2 = ET.fromstring(r2.text)
res2 = root2.find('.//{http://tempuri.org/}SearchOfferStep2Result')

if res2 is not None:
    if res2.text:
        result_root2 = ET.fromstring(res2.text)
    else:
        result_root2 = res2
    
    # Проверяем на ошибки
    error = result_root2.find('.//error')
    if error is not None:
        print(f"\n❌ Step2 ERROR: state={error.get('state')}", flush=True)
        print(f"   Message: {error.findtext('message')}", flush=True)
    else:
        # Ищем предложения
        rows = result_root2.findall('.//row')
        print(f"\n✅ Step2 SUCCESS: Found {len(rows)} offers!", flush=True)
        
        if rows:
            print(f"\nFirst 3 offers:", flush=True)
            for i, row in enumerate(rows[:3], 1):
                brand = row.findtext('ProducerName', '')
                article = row.findtext('ProductCode', '')
                name = row.findtext('ProductName', '')
                price = row.findtext('Price', '0')
                quantity = row.findtext('Quantity', '0')
                print(f"\n{i}. {brand} {article}", flush=True)
                print(f"   {name}", flush=True)
                print(f"   Price: {price} RUB, Qty: {quantity}", flush=True)

print("\n" + "="*70, flush=True)
