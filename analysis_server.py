# 필수 패키지 설치: pip install fastapi uvicorn ollama openai python-multipart python-dotenv nest-asyncio

import os
import shutil
import uvicorn
import nest_asyncio
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import ollama

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

useModel = os.getenv("USE_MODEL", "OLLAMA")
openaiKey = os.getenv("OPENAI_API_KEY")
ollamaModel = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
datasetPath = "dataset"

if not os.path.exists(datasetPath):
    os.makedirs(datasetPath)

async def analyzeWithOllama(imageBytes, userQuestion):
    try:
        response = ollama.generate(
            model=ollamaModel,
            prompt=userQuestion,
            images=[imageBytes]
        )
        return response['response']
    except Exception as e:
        return f"Ollama 에러: {str(e)}"

async def analyzeWithGpt(imageBytes, userQuestion):
    try:
        client = OpenAI(api_key=openaiKey)
        base64Image = base64.b64encode(imageBytes).decode('utf-8')
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": userQuestion},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64Image}"}}
                    ],
                }
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"GPT 에러: {str(e)}"

@app.post("/analyze")
async def analyzeImage(
    file: UploadFile = File(...),    # Node.js의 formData.append('file', ...)와 일치
    question: str = Form(...)       # Node.js의 formData.append('question', ...)와 일치
):
    try:
        imageContent = await file.read()
        
        # 이미지 저장 (백업용)
        savePath = os.path.join(datasetPath, file.filename)
        with open(savePath, "wb") as buffer:
            buffer.write(imageContent)
        
        resultText = ""
        if useModel == "GPT":
            resultText = await analyzeWithGpt(imageContent, question)
        else:
            resultText = await analyzeWithOllama(imageContent, question)

        # 프론트엔드(index.html)의 data.text, data.answer와 일치시킴
        return {
            "text": f"모델({useModel}) 분석 완료",
            "answer": resultText
        }

    except Exception as e:
        return {"text": "에러 발생", "answer": str(e)}

if __name__ == "__main__":
    nest_asyncio.apply()
    print(f"현재 활성화된 모델: {useModel}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
