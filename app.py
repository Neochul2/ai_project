# 필수 패키지 설치: pip install fastapi uvicorn ollama openai python-multipart python-dotenv nest-asyncio mysql-connector-python chandra-ocr[hf] torch torchvision pillow

import os
import shutil
import uvicorn
import nest_asyncio
import base64
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
import ollama
from PIL import Image
import io

# DB 모듈 임포트
from database import initDb, saveAnalysisResult

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# 글로벌 변수로 Chandra 매니저 관리 (지연 로딩)
chandraManager = None

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

useModelEnv = os.getenv("USE_MODEL", "OLLAMA")
openaiKey = os.getenv("OPENAI_API_KEY")
ollamaModel = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
datasetPath = "dataset"

if not os.path.exists(datasetPath):
    os.makedirs(datasetPath)

async def analyzeWithOllama(imageBytes, userQuestion):
    """ Ollama 모델을 사용하여 이미지를 분석합니다. """
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
    """ OpenAI GPT-4o 모델을 사용하여 이미지를 분석합니다. """
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
    imageFile: UploadFile = File(...),              # 필수 파일
    userQuestion: Optional[str] = Form(None),       # 선택적 질문
    modelType: Optional[str] = Form("OLLAMA")       # 모델 선택 (기본값 OLLAMA)
):
    """ 업로드된 이미지를 선택한 모델에 따라 분석하고 결과를 DB에 저장한 뒤 반환합니다. """
    try:
        # 디버깅 로그
        print(f"📥 요청 수신 - 모델: {modelType}, 파일명: {imageFile.filename}, 질문: {userQuestion}")

        imageContent = await imageFile.read()
        safeFilename = os.path.basename(imageFile.filename)
        
        # 이미지 저장 (백업용)
        savePath = os.path.join(datasetPath, safeFilename)
        with open(savePath, "wb") as buffer:
            buffer.write(imageContent)
        
        # 질문이 비어있을 경우 기본 질문 설정
        finalQuestion = userQuestion if userQuestion else "이 이미지에 대해 설명해줘."
        
        resultText = ""
        # 모델 선택에 따른 분기 처리
        if modelType == "GPT":
            resultText = await analyzeWithGpt(imageContent, finalQuestion)
        elif modelType == "CHANDRA":
            resultText = await analyzeWithChandra(imageContent, finalQuestion)
        else:
            # 기본값 OLLAMA
            resultText = await analyzeWithOllama(imageContent, finalQuestion)

        # DB에 분석 결과 저장
        saveAnalysisResult(safeFilename, finalQuestion, resultText, modelType)

        return {
            "success": True,
            "text": f"모델({modelType}) 분석 완료",
            "answer": resultText
        }

    except Exception as e:
        print(f"❌ 분석 중 에러 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False, 
                "message": str(e)
            }
        )

if __name__ == "__main__":
    # DB 초기화
    initDb()
    
    # 비동기 루프 설정 및 서버 실행
    nest_asyncio.apply()
    print(f"현재 서버 활성화 (기본 모델: {useModelEnv})")
    uvicorn.run(app, host="0.0.0.0", port=8000)
