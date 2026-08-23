import asyncio
import json
import os
import subprocess
import time
import urllib.request
import base64
import http.server
import socketserver
import threading
import tempfile
import shutil

PORT = 8765
DOCS_DIR = os.path.abspath("docs/screenshots")
os.makedirs(DOCS_DIR, exist_ok=True)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_server():
    httpd = socketserver.TCPServer(('127.0.0.1', PORT), QuietHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    return httpd

async def cdp_call(ws, method, params=None, req_id=1):
    msg = {"id": req_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(msg))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == req_id:
            return data

async def capture_screenshots():
    import websockets
    
    res = urllib.request.urlopen("http://127.0.0.1:9222/json/list")
    tabs = json.loads(res.read().decode())
    page_tab = next(t for t in tabs if t.get("type") == "page")
    ws_url = page_tab["webSocketDebuggerUrl"]
    print("Connecting to CDP at:", ws_url)

    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        req_id = 1
        
        async def call(method, params=None):
            nonlocal req_id
            req_id += 1
            return await cdp_call(ws, method, params, req_id)

        await call("Page.enable")
        await call("Runtime.enable")
        await call("Emulation.setDeviceMetricsOverride", {
            "width": 1440,
            "height": 920,
            "deviceScaleFactor": 2,
            "mobile": False
        })

        async def snap(filename, scroll_to_selector=None, scroll_y=0, wait_time=0.8):
            if scroll_to_selector:
                await call("Runtime.evaluate", {
                    "expression": f"document.querySelector('{scroll_to_selector}')?.scrollIntoView({{behavior: 'instant', block: 'center'}});"
                })
            elif scroll_y > 0:
                await call("Runtime.evaluate", {"expression": f"window.scrollTo(0, {scroll_y})"})
            await asyncio.sleep(wait_time)
            res = await call("Page.captureScreenshot", {"format": "png"})
            b64_data = res["result"]["data"]
            filepath = os.path.join(DOCS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(b64_data))
            print(f"Captured: {filename} ({os.path.getsize(filepath):,} bytes)")

        # 1. Landing Page Hero
        print("1. Capturing Landing Page Hero...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/index.html"})
        await asyncio.sleep(1.5)
        await snap("01_landing_hero.png", scroll_y=0)

        # 2. Landing Page Features
        print("2. Capturing Landing Page Features...")
        await snap("02_features_section.png", scroll_to_selector="#features")

        # Seed localStorage
        seed_js = """
        localStorage.setItem('ecovision_session', JSON.stringify({
            email: 'alisha.garg@ecovision.org',
            firstName: 'Alisha',
            lastName: 'Garg'
        }));
        localStorage.setItem('ecovision_history', JSON.stringify([
            {
                id: 1724391200000,
                timestamp: '2026-08-23T10:15:00.000Z',
                module: 'Air Quality',
                location: 'Delhi (Urban)',
                riskLevel: 'High Risk'
            },
            {
                id: 1724390000000,
                timestamp: '2026-08-23T08:30:00.000Z',
                module: 'Water Contamination',
                location: 'Bihar (Rural)',
                riskLevel: 'Critical Risk'
            },
            {
                id: 1724385000000,
                timestamp: '2026-08-22T16:45:00.000Z',
                module: 'Air Quality',
                location: 'Karnataka (Urban)',
                riskLevel: 'Low Risk'
            },
            {
                id: 1724380000000,
                timestamp: '2026-08-22T12:00:00.000Z',
                module: 'Water Contamination',
                location: 'Maharashtra (Semi-Urban)',
                riskLevel: 'Moderate Risk'
            },
            {
                id: 1724370000000,
                timestamp: '2026-08-21T09:20:00.000Z',
                module: 'Air Quality',
                location: 'Punjab (Rural)',
                riskLevel: 'Moderate Risk'
            }
        ]));
        """

        # 3. Dashboard Overview
        print("3. Capturing Dashboard Overview...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/dashboard.html"})
        await asyncio.sleep(0.8)
        await call("Runtime.evaluate", {"expression": seed_js})
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/dashboard.html"})
        await asyncio.sleep(1.2)
        await snap("03_dashboard_overview.png", scroll_y=0)

        # 4. Air Quality Prediction - Survey Form (Initial)
        print("4. Capturing Air Prediction Survey...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/air_prediction.html"})
        await asyncio.sleep(1.2)
        fill_air_js = """
        document.querySelector('select[name=\"Region\"]').value = 'North';
        document.querySelector('input[name=\"State\"]').value = 'Delhi NCR';
        document.querySelector('select[name=\"District_Type\"]').value = 'Urban';
        document.querySelector('select[name=\"season\"]').value = 'winter';
        document.querySelector('select[name=\"traffic_level\"]').value = 'high';
        document.querySelector('select[name=\"visible_haze\"]').value = 'dense';
        document.querySelector('select[name=\"smell_of_smoke\"]').value = 'strong';
        document.querySelector('select[name=\"open_burning_nearby\"]').value = 'yes';
        document.querySelector('select[name=\"ventilation_quality\"]').value = 'poor';
        document.querySelector('select[name=\"indoor_cooking_fuel\"]').value = 'biomass';
        document.querySelector('select[name=\"nearby_industry\"]').value = 'heavy';
        """
        await call("Runtime.evaluate", {"expression": fill_air_js})
        await asyncio.sleep(0.4)
        await snap("04_air_prediction_survey.png", scroll_y=0)

        # 5. Air Quality Prediction - Result Revealed
        print("5. Capturing Air Prediction Result...")
        await call("Runtime.evaluate", {"expression": "document.getElementById('air-form').dispatchEvent(new Event('submit'));"})
        await asyncio.sleep(2.0)
        await snap("05_air_prediction_result.png", scroll_y=0)

        # 6. Water Contamination Prediction - Survey Form
        print("6. Capturing Water Prediction Survey...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/water_prediction.html"})
        await asyncio.sleep(1.2)
        fill_water_js = """
        document.querySelector('select[name=\"Region\"]').value = 'East';
        document.querySelector('input[name=\"State\"]').value = 'Bihar (Ganga Basin)';
        document.querySelector('select[name=\"District_Type\"]').value = 'Rural';
        document.querySelector('select[name=\"season\"]').value = 'monsoon';
        document.querySelector('select[name=\"water_appearance\"]').value = 'muddy';
        document.querySelector('select[name=\"sewage_smell\"]').value = 'strong';
        document.querySelector('select[name=\"dead_fish_reported\"]').value = 'yes';
        document.querySelector('select[name=\"water_source\"]').value = 'river';
        document.querySelector('select[name=\"nearby_industry\"]').value = 'heavy';
        document.querySelector('select[name=\"recent_flood\"]').value = 'yes';
        """
        await call("Runtime.evaluate", {"expression": fill_water_js})
        await asyncio.sleep(0.4)
        await snap("06_water_prediction_survey.png", scroll_y=0)

        # 7. Water Contamination Prediction - Result Revealed
        print("7. Capturing Water Prediction Result...")
        await call("Runtime.evaluate", {"expression": "document.getElementById('water-form').dispatchEvent(new Event('submit'));"})
        await asyncio.sleep(2.0)
        await snap("07_water_prediction_result.png", scroll_y=0)

        # 8. Prediction History Log
        print("8. Capturing Prediction History...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/history.html"})
        await asyncio.sleep(1.2)
        await snap("08_prediction_history.png", scroll_y=0)

        # 9. About Page
        print("9. Capturing About Platform...")
        await call("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/templates/about.html"})
        await asyncio.sleep(1.2)
        await snap("09_about_architecture.png", scroll_y=0)

def main():
    httpd = start_server()
    print("HTTP Server started on 127.0.0.1:8765")
    
    tmp_user_dir = tempfile.mkdtemp()
    chrome_proc = subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        f'--user-data-dir={tmp_user_dir}',
        '--remote-debugging-port=9222',
        '--disable-gpu',
        '--no-sandbox',
        '--window-size=1440,920',
        '--hide-scrollbars'
    ])
    time.sleep(2.0)

    try:
        asyncio.run(capture_screenshots())
    finally:
        chrome_proc.terminate()
        httpd.shutdown()
        shutil.rmtree(tmp_user_dir, ignore_errors=True)
    print("All screenshots successfully refreshed in docs/screenshots/")

if __name__ == "__main__":
    main()
