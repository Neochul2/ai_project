# %% [markdown]
# ### AI 분석 서버 (FastAPI)
# 이 서버는 사용자가 업로드한 이미지를 분석하여 텍스트를 추출하고 질문에 답합니다.

# %%


# %%
# 필수 패키지 설치 가이드 (실행 전 확인)
# pip install fastapi uvicorn ollama openai python-multipart python-dotenv nest-asyncio

import os
import shutil
import uvicorn
import nest_asyncio
from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import ollama

# 환경 변수 로드
load_dotenv()

# FastAPI 설정
app = FastAPI()

# CORS 설정: 모든 Origin 허용 (*)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 설정 변수 (환경 변수에서 가져옴)
useModel = os.getenv("USE_MODEL", "OLLAMA")
openaiKey = os.getenv("OPENAI_API_KEY")
ollamaModel = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
datasetPath = "dataset"

# 데이터셋 폴더가 없으면 생성
if datasetPath not in os.listdir("."):
    os.makedirs(datasetPath)

def analyzeWithOllama(filePath, userQuestion):
    """ 
    Ollama 로컬 모델(gemma4:e2b)을 사용하여 이미지와 질문을 분석합니다. 
    """
    try:
        # 이미지 파일을 바이트 형식으로 읽음
        with open(filePath, "rb") as imgFile:
            imgBytes = imgFile.read()
        
        # Ollama API 호출
        response = ollama.chat(
            model=ollamaModel,
            messages=[{
                'role': 'user',
                'content': userQuestion,
                'images': [imgBytes]
            }]
        )
        
        return response['message']['content']
    except Exception as e:
        raise Exception(f"Ollama 분석 중 오류 발생: {str(e)}")

def analyzeWithGpt(filePath, userQuestion):
    """ 
    OpenAI GPT API를 사용하여 이미지와 질문을 분석합니다. 
    """
    try:
        client = OpenAI(api_key=openaiKey)
        
        # 분석 요청 (이미지 처리 가능 모델 gpt-4o)
        # 실제 구현 시 base64 인코딩 등이 필요할 수 있으나 구조적 예시로 작성
        # 여기서는 모델 스위칭 로직의 명확성을 보여줌
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": userQuestion},
                        # 실제 서비스 시 이미지 URL 또는 Base64 전달 로직 추가
                    ],
                }
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"GPT 분석 중 오류 발생: {str(e)}")

@app.post("/analyze")
async def analyzeImage(imageFile: UploadFile = File(...), userQuestion: str = Form(...)):
    """ 
    사용자가 업로드한 이미지를 저장하고 선택된 모델에 따라 분석 결과를 반환합니다. 
    """
    try:
        # 1. 이미지 저장 경로 설정
        savePath = os.path.join(datasetPath, imageFile.filename)
        
        # 2. 파일 저장
        with open(savePath, "wb") as buffer:
            shutil.copyfileobj(imageFile.file, buffer)
        
        # 3. 모델 선택 및 분석 실행
        resultText = ""
        if useModel == "GPT":
            resultText = analyzeWithGpt(savePath, userQuestion)
        elif useModel == "OLLAMA":
            resultText = analyzeWithOllama(savePath, userQuestion)
        else:
            resultText = "정의되지 않은 모델 설정입니다."

        # 4. 결과 반환
        return {
            "success": True,
            "model": useModel,
            "result": resultText
        }

    except Exception as e:
        # 가이드라인에 따른 에러 메시지 형식
        return {
            "success": False, 
            "message": str(e)
        }

# 주피터 노트북에서 실행을 위한 uvicorn 설정
if __name__ == "__main__":
    nest_asyncio.apply()
    print(f"현재 활성화된 모델: {useModel}")
    uvicorn.run(app, host="0.0.0.0", port=8000)


