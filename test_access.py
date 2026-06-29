import trino
import configparser
import os

def test_connection(user_email):
    print(f"\n--- Testing connection with user: {user_email} ---")
    try:
        config = configparser.ConfigParser()
        config.read(os.path.expanduser(r'C:\Users\RentoBees\Downloads\Trino_Scripts\config.ini'))
        port = config.getint('TRINO', 'port')
    except:
        port = 80
        
    try:
        conn = trino.dbapi.connect(
            host='trino-lakehouse-alb-455504457.ap-south-1.elb.amazonaws.com', 
            port=port, 
            user=user_email, 
            catalog='hive', 
            source='test_access.py' 
        )
        cur = conn.cursor()
        print("Connected to Coordinator!")
        print("Attempting to run a simple query (SHOW SCHEMAS)...")
        cur.execute("SHOW SCHEMAS")
        schemas = cur.fetchall()
        print("SUCCESS! User is AUTHORIZED.")
        print(f"Returned schemas: {[s[0] for s in schemas[:3]]}...")
    except Exception as e:
        print("FAILED! User is BLOCKED.")
        print(f"Error Message: {e}")

if __name__ == '__main__':
    print("Testing an authorized user...")
    test_connection("prabhat.sharma@credresolve.com")
    
    print("\nTesting an UNAUTHORIZED user...")
    test_connection("random.hacker@gmail.com")
