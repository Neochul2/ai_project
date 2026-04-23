import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# DB 연결 정보 (환경 변수 또는 기본값)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "ai_project_db")
DB_PORT = 3307  # 🔥 수정: 포트 추가 + int 변환

def get_db_connection():
    """MySQL 데이터베이스 연결 반환"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def init_db():
    """데이터베이스 및 테이블 초기화"""
    try:
        # DB가 없는 경우 생성을 위해 초기 연결 (database 지정 없이)
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # DB 생성
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # 테이블 생성
        create_table_query = """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255),
            question TEXT,
            answer TEXT,
            model_name VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Database '{DB_NAME}' initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def save_analysis_result(filename, question, answer, model_name):
    """분석 결과를 DB에 저장"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO analysis_results (filename, question, answer, model_name)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (filename, question, answer, model_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Analysis result saved to DB.")
    except Exception as e:
        print(f"Error saving to database: {e}")

if __name__ == "__main__":
    init_db()

print("🔥 현재 포트:", DB_PORT)