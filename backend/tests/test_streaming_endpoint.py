#!/usr/bin/env python3
"""
Script kiểm tra streaming endpoint - sử dụng thư viện chuẩn
Không cần tải thêm dependencies
"""

import urllib.request
import json
import sys
from urllib.error import URLError

# Cấu hình
API_URL = "http://localhost:8000/api/chatbot/chat-stream"
TEST_MESSAGE = "Cho tôi xem điểm của tôi"
STUDENT_ID = 1
TOKEN = "your_auth_token_here"  # Set từ env hoặc config

def test_streaming_endpoint():
    """Test streaming endpoint với Python standard library"""
    
    print("=" * 70)
    print("TESTING STREAMING ENDPOINT")
    print("=" * 70)
    print(f"\n📡 Endpoint: {API_URL}")
    print(f"📝 Message: {TEST_MESSAGE}")
    print(f"👤 Student ID: {STUDENT_ID}\n")
    
    # Prepare URL
    url = f"{API_URL}?message={urllib.parse.quote(TEST_MESSAGE)}&student_id={STUDENT_ID}"
    
    # Create request with Bearer token
    req = urllib.request.Request(
        url,
        method='POST',
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        }
    )
    
    chunk_count = 0
    try:
        print("🔄 Connecting to server...\n")
        with urllib.request.urlopen(req, timeout=30) as response:
            print("✅ Connection established\n")
            print("─" * 70)
            print("STREAMING CHUNKS:")
            print("─" * 70 + "\n")
            
            buffer = ""
            while True:
                # Read data line by line
                line = response.readline()
                if not line:
                    break
                
                line = line.decode('utf-8').strip()
                
                # Handle SSE format
                if line.startswith("data: "):
                    chunk_count += 1
                    chunk_json = line[6:]  # Remove "data: " prefix
                    
                    try:
                        chunk = json.loads(chunk_json)
                        chunk_type = chunk.get('type', 'unknown')
                        stage = chunk.get('stage', '-')
                        message = chunk.get('message', '')
                        
                        # Format output
                        print(f"Chunk #{chunk_count}: {chunk_type.upper()}")
                        print(f"  Stage: {stage}")
                        if message:
                            print(f"  Message: {message}")
                        
                        # Show data info if available
                        if chunk.get('partial_data'):
                            print(f"  Data: {len(chunk['partial_data'])} items")
                        
                        if chunk.get('data'):
                            print(f"  Full Data: {len(chunk['data'])} items")
                        
                        # Show intent/confidence for done chunks
                        if chunk_type == 'done':
                            print(f"  Intent: {chunk.get('intent')}")
                            print(f"  Confidence: {chunk.get('confidence')}")
                            print(f"  Text: {chunk.get('text')}")
                        
                        print()
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        print(f"   Raw: {chunk_json[:100]}...")
        
        print("─" * 70)
        print(f"✅ Streaming completed ({chunk_count} chunks received)\n")
        return True
        
    except URLError as e:
        if "Connection refused" in str(e):
            print("❌ Connection refused - Server not running")
            print(f"   Ensure server is running: python backend/main.py")
        else:
            print(f"❌ Connection error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_curl_example():
    """Show curl command để test"""
    print("\n" + "=" * 70)
    print("ALTERNATIVE: Using CURL (requires curl command)")
    print("=" * 70 + "\n")
    
    curl_cmd = f"""
curl -N -X POST \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Accept: text/event-stream" \\
  "http://localhost:8000/api/chatbot/chat-stream?message=Cho%20tôi%20xem%20điểm&student_id=1"
    """
    print("Command:")
    print(curl_cmd)
    print("\nOptions:")
    print("  -N          : Disable buffering (for streaming)")
    print("  -X POST     : Use POST method")
    print("  -H          : Add headers")
    print("  -A          : Accept header for SSE")


if __name__ == "__main__":
    import urllib.parse
    
    print("\n🚀 STREAMING ENDPOINT TEST SCRIPT\n")
    
    # Check if server is needed
    if len(sys.argv) > 1 and sys.argv[1] == "--curl-only":
        show_curl_example()
    else:
        success = test_streaming_endpoint()
        print("\nℹ️  For more options:")
        show_curl_example()
        
        sys.exit(0 if success else 1)
