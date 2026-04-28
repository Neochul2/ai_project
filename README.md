
Q.422 오류가 출력되고 분석서버와 연결 실패가 나오는데 바뀐 포인트 알려주고 수정해줘 



현재 상태 요약
사용자님이 수정하신 Node.js 코드는 다음과 같은 상태일 것입니다:

1 // Node.js (server.js)
2 formData.append('imageFile', imageFile.buffer, {
3     filename: imageFile.originalname, // 파일명 전달 (필수!)
4     contentType: imageFile.mimetype,   // 컨텐츠 타입 전달 (필수!)
5 });
6 formData.append('userQuestion', question || "");


1 # Python (analysis_server.py)
2 @app.post("/analyze")
3 async def analyzeImage(
4     imageFile: UploadFile = File(...), # 'file'이 아니라 'imageFile'로 일치
5     userQuestion: str = Form(...)      # 'question'이 아니라 'userQuestion'으로 일치
6 ):

원인 js api간 파일명 불일치 
구분	Node.js (보내는 쪽)	FastAPI (받는 쪽)
이미지	file	              imageFile
질문	question	          userQuestion
