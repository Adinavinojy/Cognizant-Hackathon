import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_questions_endpoint():
    print("Testing GET /questions...")
    
    # 1. Standard Request Test
    response = client.get("/questions", params={
        "role": "Backend Engineer",
        "topic": "Python / Data Structures",
        "count": 3
    })
    
    assert response.status_code == 200, f"Failed with code {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"✅ Success! Received {len(data)} questions:")
    for i, q in enumerate(data, 1):
        print(f"\n[{i}] Source: {q['source']} | Difficulty: {q['difficulty']}")
        print(f"ID: {q['question_id']}")
        print(f"Q: {q['question_text'][:90]}...")
        print(f"A: {q['reference_answer'][:90]}...")

if __name__ == "__main__":
    test_questions_endpoint()