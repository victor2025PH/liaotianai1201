#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的注册记录
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def check_registration_records(phone="+639542360349"):
    """检查注册记录"""
    print("=" * 80)
    print("Checking Database Registration Records")
    print("=" * 80)
    print(f"Phone: {phone}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Find database file
    db_paths = [
        Path("admin-backend/admin.db"),
        Path("admin-backend/data/admin.db"),
        Path("data/admin.db"),
    ]
    
    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("ERROR: Database file not found")
        print("Searched paths:")
        for path in db_paths:
            print(f"  {path}")
        return
    
    print(f"Database: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all registrations for this phone
        cursor.execute("""
            SELECT id, phone, status, phone_code_hash, created_at, updated_at, 
                   error_message, retry_count, node_id
            FROM user_registrations
            WHERE phone = ? OR phone = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (phone, phone.replace('+', '')))
        
        records = cursor.fetchall()
        
        if not records:
            print(f"No registration records found for {phone}")
        else:
            print(f"Found {len(records)} registration records:")
            print()
            
            # Group by status
            status_groups = {}
            for record in records:
                status = record[2]
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(record)
            
            for status, group_records in status_groups.items():
                print(f"Status: {status} ({len(group_records)} records)")
                print("-" * 80)
                
                for record in group_records:
                    reg_id, reg_phone, status, phone_code_hash, created_at, updated_at, error_message, retry_count, node_id = record
                    
                    print(f"  Registration ID: {reg_id}")
                    print(f"    Phone: {reg_phone}")
                    print(f"    Node ID: {node_id}")
                    print(f"    Phone Code Hash: {phone_code_hash}")
                    print(f"    Created At: {created_at}")
                    print(f"    Updated At: {updated_at}")
                    print(f"    Retry Count: {retry_count}")
                    if error_message:
                        print(f"    Error: {error_message}")
                    
                    # Calculate time difference
                    if created_at and updated_at:
                        try:
                            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            time_diff = (updated - created).total_seconds()
                            print(f"    Time Difference: {time_diff:.1f} seconds ({time_diff/60:.2f} minutes)")
                        except:
                            pass
                    
                    print()
            
            # Check for multiple code_sent records with different hashes
            cursor.execute("""
                SELECT phone_code_hash, COUNT(*) as count
                FROM user_registrations
                WHERE (phone = ? OR phone = ?) 
                  AND status = 'code_sent' 
                  AND phone_code_hash IS NOT NULL
                GROUP BY phone_code_hash
                HAVING COUNT(*) > 0
            """, (phone, phone.replace('+', '')))
            
            hash_groups = cursor.fetchall()
            if len(hash_groups) > 1:
                print("WARNING: Multiple different phone_code_hash values found!")
                print("-" * 80)
                for hash_val, count in hash_groups:
                    print(f"  Hash: {hash_val} (used {count} times)")
                print()
                print("This indicates multiple 'start registration' clicks!")
                print("Each click generates a new hash, making old verification codes invalid.")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("Check Complete")
    print("=" * 80)

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else "+639542360349"
    check_registration_records(phone)

