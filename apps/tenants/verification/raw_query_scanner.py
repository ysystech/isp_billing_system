"""
Script to scan codebase for raw SQL queries and potential tenant isolation issues.
"""
import os
import re
from pathlib import Path


class RawQueryScanner:
    """Scan codebase for raw SQL queries that might bypass tenant filtering."""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.issues = []
        self.raw_query_patterns = [
            (r'\.raw\s*\(', 'Raw query usage'),
            (r'connection\.execute\s*\(', 'Direct SQL execution'),
            (r'cursor\.execute\s*\(', 'Cursor execute'),
            (r'connection\.cursor\s*\(\)', 'Direct cursor usage'),
            (r'SELECT.*FROM\s+\w+', 'SQL SELECT statement'),
            (r'UPDATE\s+\w+\s+SET', 'SQL UPDATE statement'),
            (r'DELETE\s+FROM\s+\w+', 'SQL DELETE statement'),
            (r'INSERT\s+INTO\s+\w+', 'SQL INSERT statement'),
        ]
        
        self.exempt_files = [
            'migrations/',
            'test_',
            '__pycache__/',
            '.pyc',            'verify_tenant_isolation.py',
            'raw_query_scanner.py',
            'query_logger.py',
        ]
    
    def scan(self):
        """Scan all Python files for raw queries."""
        print('\n🔍 Scanning for raw SQL queries...')
        
        for py_file in self.project_root.rglob('*.py'):
            # Skip exempt files
            if any(exempt in str(py_file) for exempt in self.exempt_files):
                continue
            
            self.scan_file(py_file)
        
        self.print_results()
    
    def scan_file(self, file_path):
        """Scan a single file for raw queries."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern, description in self.raw_query_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if it's in a comment
                        if line.strip().startswith('#') or line.strip().startswith('//'):
                            continue                        
                        # Check if tenant filtering is nearby
                        if not self.has_tenant_filter_nearby(content, line_num):
                            self.issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'type': description,
                                'code': line.strip()
                            })
                        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
    
    def has_tenant_filter_nearby(self, content, line_num, context=5):
        """Check if tenant filtering exists near the raw query."""
        lines = content.splitlines()
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        
        nearby_lines = lines[start:end]
        nearby_text = '\n'.join(nearby_lines)
        
        tenant_indicators = [
            'tenant_id',
            'tenant=',
            'filter(tenant=',
            '.tenant',
            'request.tenant',
        ]
        
        return any(indicator in nearby_text for indicator in tenant_indicators)
    def print_results(self):
        """Print scan results."""
        print('\n' + '='*60)
        print('RAW QUERY SCAN RESULTS')
        print('='*60)
        
        if not self.issues:
            print('\n✅ No suspicious raw queries found!')
        else:
            print(f'\n⚠️  Found {len(self.issues)} potential issues:')
            
            # Group by file
            by_file = {}
            for issue in self.issues:
                if issue['file'] not in by_file:
                    by_file[issue['file']] = []
                by_file[issue['file']].append(issue)
            
            for file_path, file_issues in by_file.items():
                print(f'\n📄 {file_path}:')
                for issue in file_issues:
                    print(f"   Line {issue['line']}: {issue['type']}")
                    print(f"   > {issue['code'][:80]}..." if len(issue['code']) > 80 else f"   > {issue['code']}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:        project_root = sys.argv[1]
    else:
        project_root = '/Users/aldesabido/pers/isp_billing_system'
    
    scanner = RawQueryScanner(project_root)
    scanner.scan()