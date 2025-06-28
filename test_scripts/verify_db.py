"""
Database verification for geo-location fields
Run with: make manage ARGS="shell < test_scripts/verify_db.py"
"""

from django.db import connection

print("Checking database schema for geo-location fields...\n")

# Check each table
tables_to_check = [
    ('customers_customer', 'Customer'),
    ('lcp_lcp', 'LCP'),
    ('lcp_splitter', 'Splitter'),
    ('lcp_nap', 'NAP')
]

geo_columns = ['latitude', 'longitude', 'location_accuracy', 'location_notes']
extra_columns = {
    'lcp_lcp': ['coverage_radius_meters'],
    'lcp_nap': ['max_distance_meters']
}

with connection.cursor() as cursor:
    for table_name, model_name in tables_to_check:
        print(f"Checking {model_name} table ({table_name}):")
        
        # Get column info
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            AND column_name IN %s
            ORDER BY column_name
        """, [table_name, tuple(geo_columns + extra_columns.get(table_name, []))])
        
        columns = cursor.fetchall()
        
        if columns:
            for col_name, data_type, nullable in columns:
                print(f"  ✓ {col_name}: {data_type} (nullable: {nullable})")
        else:
            print(f"  ✗ No geo-location columns found!")
        
        print()

print("Database verification complete!")
