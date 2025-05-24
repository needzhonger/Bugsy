import mysql.connector
from mysql.connector import Error

# 连接到 MySQL 数据库
def create_connection():
    return mysql.connector.connect(
        host='sql.wsfdb.cn',
        port=3306,
        user='13581867031Bugsyusersdata',  # 替换为您的数据库用户名
        password='501314',  # 替换为您的数据库密码
        database='13581867031Bugsyusersdata',  # 替换为您的数据库名称
        ssl_disabled = True
    )

# 注册用户
def register_user(username, password):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (username VARCHAR(255) PRIMARY KEY, password VARCHAR(255), history TEXT)")
        cursor.execute("INSERT INTO users (username, password, history) VALUES (%s, %s, %s)", (username, password, '[]'))
        connection.commit()
        return True
    except Error as e:
        print(f"数据库错误：{e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("数据库连接已关闭。")

# 用户登录
def login_user(username, password):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        return user is not None
    except Error as e:
        print(f"数据库错误：{e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()