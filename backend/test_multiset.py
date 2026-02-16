import os
import sys
import base64
from fastapi.testclient import TestClient
from main import app

# Add current directory to path so we can import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)

def test_generate_multiset():
    # 1x1 pixel red dot base64
    dummy_img = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9U6KKKAP/2Q=="

    payload = {
        "units": [
            {
                "nopol": "B 1234 TEST",
                "bu": "TEST_BU",
                "lokasi": "TEST_LOC",
                "images": {
                    "front": dummy_img,
                    "back": dummy_img,
                    "stnk": dummy_img
                }
            },
            {
                "nopol": "D 5678 DEMO",
                "bu": "TEST_BU",
                "lokasi": "TEST_LOC",
                "images": {
                    "right": dummy_img,
                    "tax": dummy_img
                }
            }
        ]
    }

    print("Sending request...")
    response = client.post("/generate-multiset", json=payload)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    
    # Save output
    with open("test_output.pdf", "wb") as f:
        f.write(response.content)
    print("PDF saved to test_output.pdf")

if __name__ == "__main__":
    test_generate_multiset()
