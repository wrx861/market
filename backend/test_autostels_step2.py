#!/usr/bin/env python3
import requests
import base64
import xml.etree.ElementTree as ET
import sys

login_b64 = base64.b64encode(b'car.workshop72@mail.ru').decode()
password_b64 = base64.b64encode(b'Qq23321q').decode()

print("="*70, flush=True)
print("TEST: Autostels Step2 with different formats", flush=True)
print("="*70, flush=True)

# Test without ResultFilter, without PeriodMin/PeriodMax
xml2_v1 = f'''<root>
   <SessionInfo ParentID="39151" UserLogin="{login_b64}" UserPass="{password_b64}" />
   <Search>
      <ProductID>25083996</ProductID>
      <StocksOnly>0</StocksOnly>
      <InStock>1</InStock>
      <ShowCross>2</ShowCross>
   </Search>
</root>'''

soap2 = f'''<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
<soapenv:Body>
<tem:SearchOfferStep2>
<tem:SearchParametersXml><![CDATA[{xml2_v1}]]></tem:SearchParametersXml>
</tem:SearchOfferStep2>
</soapenv:Body>
</soapenv:Envelope>'''

try:
    r2 = requests.post(
        'https://services.allautoparts.ru/WebService2/SearchService.svc',
        data=soap2.encode('utf-8'),
        headers={
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://tempuri.org/IAS2CSearch/SearchOfferStep2'
        },
        timeout=10
    )
    
    print(f"\n✅ HTTP Status: {r2.status_code}\n", flush=True)
    print(f"Response text length: {len(r2.text)}", flush=True)
    
    root2 = ET.fromstring(r2.text)
    res2 = root2.find('.//{http://tempuri.org/}SearchOfferStep2Result')
    
    print(f"Result element found: {res2 is not None}", flush=True)
    
    if res2 and res2.text:
        result_xml = res2.text
        print(f"Response length: {len(result_xml)} characters\n")
        print("First 1000 characters of response:")
        print(result_xml[:1000])
        print("\n" + "="*70)
        
        # Parse and check for errors
        result_root = ET.fromstring(result_xml)
        error = result_root.find('.//error')
        
        if error is not None:
            print(f"\n❌ ERROR: state={error.get('state')}")
            print(f"   Message: {error.findtext('message')}")
        else:
            rows = result_root.findall('.//row')
            print(f"\n✅ SUCCESS: Found {len(rows)} offers!")
            if rows:
                print("\nFirst offer:")
                for child in rows[0]:
                    print(f"  {child.tag}: {child.text}")
    
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
