import trino

def test_random_user():
    fake_email = "totally_fake_random_user@doesnotexist.com"
    print(f"Attempting to connect to Trino as: {fake_email}")
    
    try:
        conn = trino.dbapi.connect(
            host='trino-lakehouse-alb-455504457.ap-south-1.elb.amazonaws.com',
            port=80,
            user=fake_email,
            catalog='system'
        )
        cur = conn.cursor()
        
        # Test 1: SELECT 1
        print("Testing SELECT 1...")
        cur.execute("SELECT 1")
        print("SUCCESS! SELECT 1 ran:", cur.fetchall())
        
        # Test 2: Accessing system catalog tables
        print("Testing SHOW SCHEMAS IN system...")
        cur.execute("SHOW SCHEMAS IN system")
        print("SUCCESS! SHOW SCHEMAS ran:", cur.fetchall())
        
    except Exception as e:
        print("\nERROR! Trino rejected the query.")
        print(f"Exact error message: {e}")

if __name__ == '__main__':
    test_random_user()
