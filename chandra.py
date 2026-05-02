# 필수 패키지 설치: pip install fastapi uvicorn chandra-ocr torch torchvision pillow mysql-connector-python python-dotenv python-multipart

import os
import uvicorn
import nest_asyncio
import io
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from PIL import Image

# DB 모듈 임포트 (기존 database.py 공유)
from database import initDb, saveAnalysisResult

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="Chandra OCR Dedicated Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

datasetPath = "dataset"
chandraManager = None

if not os.path.exists(datasetPath):
    os.makedirs(datasetPath)

async def analyzeWithChandra(imageBytes):
    """ Chandra OCR 2 모델을 사용하여 텍스트를 추출합니다. """
    global chandraManager
    try:
        from chandra.model import InferenceManager
        from chandra.model.schema import BatchInputItem
        
        if chandraManager is None:
            print("⏳ Chandra 모델 로딩 중 (Hugging Face)...")
            chandraManager = InferenceManager(method="hf")
        
        image = Image.open(io.BytesIO(imageBytes))
        batch = [BatchInputItem(image=image, prompt_type="ocr_layout")]
        resultList = chandraManager.generate(batch)
        
        if resultList and len(resultList) > 0:
            result = resultList[0]
            return result.markdown if hasattr(result, 'markdown') else str(result)
        return "분석 결과 없음"
    except Exception as e:
        print(f"❌ OCR 에러: {str(e)}")
        return f"OCR 에러: {str(e)}"

@app.post("/ocr")
async def performOcr(
    imageFile: UploadFile = File(...),
    userQuestion: Optional[str] = Form(None)
):
    """ 이미지 업로드 및 OCR 수행 엔드포인트 """
    try:
        print(f"📥 [Chandra 서버] 요청 수신: {imageFile.filename}")
        
        imageContent = await imageFile.read()
        safeFilename = os.path.basename(imageFile.filename)
        
        # 이미지 저장
        savePath = os.path.join(datasetPath, safeFilename)
        with open(savePath, "wb") as buffer:
            buffer.write(imageContent)
        
        # OCR 분석
        resultText = await analyzeWithChandra(imageContent)
        
        # DB 저장
        finalQuestion = userQuestion if userQuestion else "이미지 OCR 분석"
        saveAnalysisResult(safeFilename, finalQuestion, resultText, "CHANDRA")
        
        return {
            "success": True,
            "filename": safeFilename,
            "ocr_result": resultText
        }
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

if __name__ == "__main__":
    initDb()
    nest_asyncio.apply()
    print("🚀 Chandra OCR 전용 서버 시작 (chandra.py, Port: 8001)")
    uvicorn.run(app, host="0.0.0.0", port=8001)
