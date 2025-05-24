import mysql.connector
import json
from mysql.connector import Error

# 建立数据库连接
def create_connection():
    return mysql.connector.connect(
        host='sql.wsfdb.cn',
        port=3306,
        user='13581867031Bugsyusersdata',
        password='501314',
        database='13581867031Bugsyusersdata',
        ssl_disabled=True
    )

# 读取用户历史记录
def get_user_history(username):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()
        query = "SELECT history FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result:
            history_json = result[0]
            return json.loads(history_json)
        else:
            return []
    except Error as e:
        print(f"数据库错误：{e}")
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 添加一条历史记录
def add_user_history(username, new_entry):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()
        # 获取当前历史记录
        query = "SELECT history FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result:
            history = json.loads(result[0])
        else:
            history = []
        # 添加新记录
        history.append(new_entry)
        # 更新数据库中的历史记录
        update_query = "UPDATE users SET history = %s WHERE username = %s"
        cursor.execute(update_query, (json.dumps(history), username))
        connection.commit()
        return True
    except Error as e:
        print(f"数据库错误：{e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()