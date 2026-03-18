from db import get_conn

conn = get_conn()
cur = conn.cursor()


    
conn.commit()
conn.close()
print("Migration done")