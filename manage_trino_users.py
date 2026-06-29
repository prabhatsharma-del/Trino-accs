import boto3
import json
import time

# =====================================================================
# TRINO USERS LIST
# =====================================================================
# ADMINS: Can read, write, create, and drop tables. (Full Access)
ADMIN_EMAILS = [
    "prabhat.sharma@credresolve.com",
    "admin"
]

# READ-ONLY USERS: Can only run SELECT queries. Cannot modify data.
READ_ONLY_EMAILS = [
    # "john.doe@credresolve.com", 
]

COORD_IP = "172.31.22.113"
# =====================================================================

def load_credentials():
    import configparser
    import os
    config = configparser.ConfigParser()
    config.read(os.path.expanduser(r'C:\Users\RentoBees\.aws\credentials'))
    ak = config.get('default', 'aws_access_key_id')
    sk = config.get('default', 'aws_secret_access_key')
    return ak, sk

def main():
    print("Gathering AWS credentials...")
    try:
        ak, sk = load_credentials()
        session = boto3.Session(aws_access_key_id=ak, aws_secret_access_key=sk, region_name='ap-south-1')
    except Exception as e:
        print("ERROR: Could not load AWS credentials:", e)
        return
        
    ec2 = session.client('ec2')
    ssm = session.client('ssm')

    print(f"Finding Trino Coordinator Instance ID for {COORD_IP}...")
    resp = ec2.describe_instances(Filters=[
        {'Name': 'private-ip-address', 'Values': [COORD_IP]},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ])
    coord_id = None
    for res in resp.get('Reservations', []):
        for inst in res.get('Instances', []):
            coord_id = inst['InstanceId']
            break
    if not coord_id:
        print("ERROR: Coordinator not found or not running!")
        return

    print(f"Coordinator Instance ID: {coord_id}")
    
    # Generate rules.json
    rules = {
        "queries": [],
        "catalogs": []
    }
    
    for email in ADMIN_EMAILS:
        escaped_email = email.replace('.', '\\.')
        rules["queries"].append({
            "user": f"^{escaped_email}$",
            "allow": ["execute", "kill", "view"]
        })
        rules["catalogs"].append({
            "user": f"^{escaped_email}$",
            "catalog": ".*",
            "allow": "all"
        })
        
    for email in READ_ONLY_EMAILS:
        escaped_email = email.replace('.', '\\.')
        rules["queries"].append({
            "user": f"^{escaped_email}$",
            "allow": ["execute", "view"]
        })
        rules["catalogs"].append({
            "user": f"^{escaped_email}$",
            "catalog": ".*",
            "allow": "read-only"
        })
    
    # default deny all
    rules["queries"].append({
        "allow": []
    })
    rules["catalogs"].append({
        "catalog": ".*",
        "allow": "none"
    })
    
    rules_json_str = json.dumps(rules, indent=2)
    print("\n--- Generated rules.json ---")
    print(rules_json_str)
    print("----------------------------\n")
    
    # Shell script to apply config
    script = f"""#!/bin/bash
set -e

echo "1. Creating /opt/trino/etc/rules.json..."
cat << 'EOF' > /opt/trino/etc/rules.json
{rules_json_str}
EOF

echo "2. Enabling File Based System Access Control..."
cat << 'EOF' > /opt/trino/etc/access-control.properties
access-control.name=file
security.config-file=etc/rules.json
EOF

echo "3. Restarting Trino Coordinator..."
/opt/trino/bin/launcher restart
sleep 15
/opt/trino/bin/launcher status

echo "Update Complete."
"""

    print("Deploying configuration to Coordinator via SSM (this takes about 20-30 seconds)...")
    r = ssm.send_command(
        InstanceIds=[coord_id],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': [script]},
        TimeoutSeconds=300
    )
    cid = r['Command']['CommandId']
    
    while True:
        time.sleep(5)
        try:
            inv = ssm.get_command_invocation(CommandId=cid, InstanceId=coord_id)
            status = inv['Status']
            print(f"Status: {status}...")
            if status not in ('Pending', 'InProgress'):
                out = inv.get('StandardOutputContent', '')
                err = inv.get('StandardErrorContent', '')
                if out:
                    print("\n--- Output ---")
                    print(out.strip())
                if err and "WARNING" not in err:
                    print("\n--- Error ---")
                    print(err.strip())
                break
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
