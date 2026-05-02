import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# DB 연결 정보 (환경 변수 또는 기본값)
dbHost = os.getenv("DB_HOST", "localhost")
dbUser = os.getenv("DB_USER", "kopo")
dbPassword = os.getenv("DB_PASSWORD", "kopo")
dbName = os.getenv("DB_NAME", "ai_project_db")
dbPort = 3307  # 수정: 문자열 "3307" 에서 int 3307로 수정 

def getDbConnection():
    """ MySQL 데이터베이스 연결을 생성하여 반환합니다. """
    return mysql.connector.connect(
        host=dbHost,
        user=dbUser,
        password=dbPassword,
        database=dbName,
        port=dbPort
    )

def initDb():
    """ 데이터베이스와 필요한 테이블을 초기화합니다. """
    try:
        # DB가 없는 경우 생성을 위해 초기 연결 (database 지정 없이)
        conn = mysql.connector.connect(
            host=dbHost,
            user=dbUser,
            password=dbPassword,
            port=dbPort
        )
        cursor = conn.cursor()
        
        # DB 생성
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbName}")
        cursor.execute(f"USE {dbName}")
        
        # 테이블 생성
        createTableQuery = """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255),
            question TEXT,
            answer TEXT,
            model_name VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(createTableQuery)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"데이터베이스 '{dbName}' 초기화 성공.")
    except Exception as e:
        print(f"데이터베이스 초기화 에러: {e}")

def saveAnalysisResult(filename, question, answer, modelName):
    """ 분석된 결과를 MySQL 데이터베이스에 저장합니다. """
    try:
        conn = getDbConnection()
        cursor = conn.cursor()
        
        insertQuery = """
        INSERT INTO analysis_results (filename, question, answer, model_name)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insertQuery, (filename, question, answer, modelName))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("분석 결과가 DB에 저장되었습니다.")
    except Exception as e:
        print(f"DB 저장 에러: {e}")

if __name__ == "__main__":
    initDb()

print("🔥 현재 DB 포트:", dbPort)