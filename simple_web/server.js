/**
 * 설치 명령어: npm install express multer axios cors
 * 실행 명령어: node server.js
 */

const express = require('express');
const multer = require('multer');
const axios = require('axios');
const cors = require('cors');
const path = require('path');
const FormData = require('form-data');

const app = express();
const PORT = 3000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // public 폴더의 정적 파일 서비스

// 메모리에 이미지 저장을 위한 Multer 설정
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// 이미지 분석 API (FastAPI 서버로 요청을 전달하는 Proxy)
app.post('/analyze', upload.single('image'), async (req, res) => {
    try {
        const { question } = req.body;
        const imageFile = req.file;

        if (!imageFile) {
            return res.status(400).json({ error: '이미지를 업로드해주세요.' });
        }

        // FastAPI 서버로 보낼 FormData 구성
        const formData = new FormData();
        formData.append('imageFile', imageFile.buffer, {
            filename: imageFile.originalname,
            contentType: imageFile.mimetype,
        });
        formData.append('userQuestion', question || "");

        // FastAPI 서버(8000 포트)로 분석 요청 전달
        const response = await axios.post('http://localhost:8000/analyze', formData, {
            headers: {
                ...formData.getHeaders(),
            },
        });

        // FastAPI로부터 받은 결과 반환
        res.json(response.data);

    } catch (error) {
        console.error('Error during analysis:', error.message);
        res.status(500).json({ 
            error: 'AI 분석 서버 연결에 실패했습니다.',
            details: error.message 
        });
    }
});

app.listen(PORT, () => {
    console.log(`서버 실행 중: http://localhost:${PORT}`);
});
