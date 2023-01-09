import psycopg2

class DatabaseConfig:
    conn = psycopg2.connect(dbname='barsik_db', user='boris', password='stiv', host='localhost')
    cursor = conn.cursor()
    
    
def add_message_to_database(message, file_name=None):
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.message_id
    reply_id = message.reply_to_message.message_id if message.reply_to_message else None
    text = message.text
    
    try:
    # print((user_id, chat_id, message_id, reply_id, text, file_name))
        DatabaseConfig.cursor.execute('INSERT INTO message (user_id, chat_id, message_id, reply_id, text, file_name) \
            values (%s, %s, %s, %s, %s, %s)', (user_id, chat_id, message_id, reply_id, text, file_name))
        DatabaseConfig.conn.commit()
    except Exception as e:
        DatabaseConfig.cursor.execute('ROLLBACK')
        DatabaseConfig.conn.commit()

# def add_response_to_database(message_id, filename):
#     DatabaseConfig.cursor.execute(f'INSERT INTO response (message_id, filename) values {(message_id, filename)}')
#     DatabaseConfig.conn.commit()


# def add_reaction_to_database(user_id, chat_id, message_id, good_or_bad):
    
    
def add_reaction_to_database(message, call_from_id, likes):
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.message_id
    
    try:
        DatabaseConfig.cursor.execute('INSERT INTO reaction (user_id, chat_id, message_id, call_from_id, likes) \
            values (%s, %s, %s, %s, %s)', (user_id, chat_id, message_id, call_from_id, likes))
        DatabaseConfig.conn.commit()
    except Exception as e:
        DatabaseConfig.cursor.execute('ROLLBACK')
        DatabaseConfig.conn.commit()

        
def add_message_to_favorite(message, call_from_id):
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_id = message.message_id
    
    try:
        DatabaseConfig.cursor.execute('INSERT INTO favorite (user_id, chat_id, message_id, call_from_id) \
            values (%s, %s, %s, %s)', (user_id, chat_id, message_id, call_from_id))
        DatabaseConfig.conn.commit()
    except Exception as e:
        DatabaseConfig.cursor.execute('ROLLBACK')
        DatabaseConfig.conn.commit()