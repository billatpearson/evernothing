"""
EverNothing Test Dashboard
Compares local and cloud test results

Usage:
  python test_dashboard.py

Access:
  http://127.0.0.1:5001/dashboard
"""

from flask import Flask, render_template_string
import subprocess
import json
import datetime
import os
import sys

app = Flask(__name__)
BUILD_DATE = datetime.datetime.now().strftime("%m/%d/%y:%H:%M")

STYLE = """
<style>
body { background-color: black; color: gold; font-family: monospace; padding: 20px; }
h1, h2, h3 { color: gold; }
a { color: gold; text-decoration: none; }
a:hover { color: red; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; }
th, td { padding: 10px; text-align: left; border: 1px solid red; }
th { background-color: #1a1a1a; color: gold; }
.pass { color: #0f0; }
.fail { color: #f00; }
.error { color: #ff0; }
.skip { color: #888; }
.summary { background-color: #1a1a1a; padding: 15px; margin: 20px 0; border: 2px solid red; }
.metric { display: inline-block; margin: 10px 20px; }
.refresh { background-color: #1a1a1a; color: gold; border: 2px solid red; padding: 10px 20px; cursor: pointer; }
.refresh:hover { background-color: red; }
.footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: black; color: gold; text-align: center; padding: 10px; }
</style>
"""

T_DASHBOARD = STYLE + """
<h1>EverNothing Test Dashboard</h1>
<p><a href="/dashboard">[Refresh]</a> | <a href="/run_tests">[Run All Tests]</a></p>

<div class="summary">
<h2>Test Summary</h2>
<div class="metric"><strong>Local Tests:</strong> {{ local_summary.total }} total, 
<span class="pass">{{ local_summary.passed }} passed</span>, 
<span class="fail">{{ local_summary.failed }} failed</span>, 
<span class="error">{{ local_summary.errors }} errors</span></div>
<div class="metric"><strong>Cloud Tests:</strong> {{ cloud_summary.total }} total, 
<span class="pass">{{ cloud_summary.passed }} passed</span>, 
<span class="fail">{{ cloud_summary.failed }} failed</span>, 
<span class="error">{{ cloud_summary.errors }} errors</span></div>
<div class="metric"><strong>Android Tests:</strong> {{ android_summary.total }} total, 
<span class="pass">{{ android_summary.passed }} passed</span>, 
<span class="fail">{{ android_summary.failed }} failed</span>, 
<span class="error">{{ android_summary.errors }} errors</span></div>
<div class="metric"><strong>Last Run:</strong> {{ last_run }}</div>
</div>

<h2>Local Tests (evernothing.py)</h2>
<table>
<tr><th>Test Name</th><th>Status</th><th>Duration</th><th>Message</th></tr>
{% for test in local_tests %}
<tr>
<td>{{ test.name }}</td>
<td class="{{ test.status }}">{{ test.status.upper() }}</td>
<td>{{ test.duration }}s</td>
<td>{{ test.message }}</td>
</tr>
{% endfor %}
</table>

<h2>Cloud Tests (S3 Sync)</h2>
<table>
<tr><th>Test Name</th><th>Status</th><th>Duration</th><th>Message</th></tr>
{% for test in cloud_tests %}
<tr>
<td>{{ test.name }}</td>
<td class="{{ test.status }}">{{ test.status.upper() }}</td>
<td>{{ test.duration }}s</td>
<td>{{ test.message }}</td>
</tr>
{% endfor %}
</table>

<h2>Android Tests</h2>
<table>
<tr><th>Test Name</th><th>Status</th><th>Duration</th><th>Message</th></tr>
{% for test in android_tests %}
<tr>
<td>{{ test.name }}</td>
<td class="{{ test.status }}">{{ test.status.upper() }}</td>
<td>{{ test.duration }}s</td>
<td>{{ test.message }}</td>
</tr>
{% endfor %}
</table>

<h2>Comparison Matrix</h2>
<table>
<tr><th>Metric</th><th>Local</th><th>Cloud</th><th>Android</th><th>Difference</th></tr>
<tr>
<td>Total Tests</td>
<td>{{ local_summary.total }}</td>
<td>{{ cloud_summary.total }}</td>
<td>{{ android_summary.total }}</td>
<td>{{ local_summary.total + cloud_summary.total + android_summary.total }}</td>
</tr>
<tr>
<td>Pass Rate</td>
<td class="pass">{{ local_summary.pass_rate }}%</td>
<td class="pass">{{ cloud_summary.pass_rate }}%</td>
<td class="pass">{{ android_summary.pass_rate }}%</td>
<td>{{ ((local_summary.pass_rate + cloud_summary.pass_rate + android_summary.pass_rate) / 3)|round(1) }}%</td>
</tr>
<tr>
<td>Execution Time</td>
<td>{{ local_summary.duration }}s</td>
<td>{{ cloud_summary.duration }}s</td>
<td>{{ android_summary.duration }}s</td>
<td>{{ (local_summary.duration + cloud_summary.duration + android_summary.duration)|round(2) }}s</td>
</tr>
</table>

<div class="footer">{{ build_date }}</div>
"""

def run_tests(test_file, test_dir='.'):
    """Run tests and parse results"""
    try:
        result = subprocess.run(
            [sys.executable, test_file, '-v'],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        tests = []
        lines = result.stderr.split('\n')
        
        for line in lines:
            if line.startswith('test_'):
                parts = line.split(' ... ')
                if len(parts) == 2:
                    name = parts[0]
                    status_msg = parts[1].strip()
                    
                    if status_msg == 'ok':
                        status = 'pass'
                        message = ''
                    elif 'FAIL' in status_msg:
                        status = 'fail'
                        message = status_msg
                    elif 'ERROR' in status_msg:
                        status = 'error'
                        message = status_msg
                    elif 'skipped' in status_msg:
                        status = 'skip'
                        message = status_msg
                    else:
                        status = 'unknown'
                        message = status_msg
                    
                    tests.append({
                        'name': name,
                        'status': status,
                        'duration': 0.0,
                        'message': message
                    })
        
        # Parse summary
        summary_line = [l for l in lines if 'Ran' in l]
        total = len(tests)
        passed = len([t for t in tests if t['status'] == 'pass'])
        failed = len([t for t in tests if t['status'] == 'fail'])
        errors = len([t for t in tests if t['status'] == 'error'])
        
        return tests, {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': round((passed / total * 100) if total > 0 else 0, 1),
            'duration': 0.0
        }
    except Exception as e:
        return [], {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'pass_rate': 0,
            'duration': 0.0
        }

@app.route('/dashboard')
def dashboard():
    # Run local tests
    local_tests, local_summary = run_tests('test_evernothing.py')
    
    # Run cloud tests (S3)
    cloud_tests, cloud_summary = run_tests('test_s3.py')
    
    # Run Android tests
    android_tests, android_summary = run_tests('test_android.py', 'android')
    
    last_run = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    
    return render_template_string(
        T_DASHBOARD,
        local_tests=local_tests,
        cloud_tests=cloud_tests,
        android_tests=android_tests,
        local_summary=local_summary,
        cloud_summary=cloud_summary,
        android_summary=android_summary,
        last_run=last_run,
        build_date=BUILD_DATE
    )

@app.route('/run_tests')
def run_all_tests():
    """Trigger test execution and redirect to dashboard"""
    return dashboard()

@app.route('/')
def index():
    return '<html><body style="background:black;color:gold;font-family:monospace;padding:50px;text-align:center;"><h1>EverNothing Test Dashboard</h1><p><a href="/dashboard" style="color:gold;font-size:24px;">View Dashboard</a></p></body></html>'

if __name__ == '__main__':
    print("=" * 60)
    print("EverNothing Test Dashboard")
    print("=" * 60)
    print(f"Dashboard URL: http://127.0.0.1:5001/dashboard")
    print(f"Started: {BUILD_DATE}")
    print("-" * 60)
    app.run(host='0.0.0.0', port=5001, debug=False)
