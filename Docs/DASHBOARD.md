# EverNothing Test Dashboard

## Overview
Web-based dashboard comparing local, cloud, and Android test results in real-time.

## Features
- **Live Test Execution**: Run all tests with one click
- **Comparison Matrix**: Side-by-side comparison of test suites
- **Visual Status**: Color-coded pass/fail indicators
- **Metrics**: Pass rates, execution times, test counts
- **Auto-refresh**: Real-time updates
- **EverNothing Theme**: Black/gold/red color scheme

## Quick Start

```bash
# Start dashboard
python test_dashboard.py

# Access in browser
http://127.0.0.1:5001/dashboard
```

## Dashboard URL

**Primary Access:**
```
http://127.0.0.1:5001/dashboard
```

**Network Access (from other devices):**
```
http://YOUR_IP:5001/dashboard
```

Find your IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `ip addr`

## Test Suites Monitored

### 1. Local Tests (`test_evernothing.py`)
- User authentication
- Note CRUD operations
- Folder management
- Encryption
- Audit logging
- Admin functions

### 2. Cloud Tests (`test_s3.py`)
- S3 connection
- Bucket operations
- File upload/download
- Credential management
- Error handling

### 3. Android Tests (`test_android.py`)
- API client
- Authentication
- Folder operations
- Note creation
- Session management

## Dashboard Sections

### Test Summary
- Total tests per suite
- Pass/fail/error counts
- Pass rate percentages
- Last run timestamp

### Individual Test Results
- Test name
- Status (pass/fail/error/skip)
- Duration
- Error messages

### Comparison Matrix
- Total tests across all suites
- Average pass rate
- Total execution time
- Performance metrics

## Usage

### View Dashboard
```bash
python test_dashboard.py
# Open: http://127.0.0.1:5001/dashboard
```

### Run Tests Manually
```bash
# Local tests
python test_evernothing.py -v

# Cloud tests
python test_s3.py -v

# Android tests
cd android
python test_android.py -v
```

### Refresh Results
Click **[Refresh]** link in dashboard or reload page

### Run All Tests
Click **[Run All Tests]** link to execute all test suites

## Configuration

### Change Port
Edit `test_dashboard.py`:
```python
app.run(host='0.0.0.0', port=5001)  # Change 5001 to desired port
```

### Add Custom Tests
1. Create test file: `test_custom.py`
2. Add to dashboard:
```python
custom_tests, custom_summary = run_tests('test_custom.py')
```

## Metrics Explained

### Pass Rate
```
Pass Rate = (Passed Tests / Total Tests) × 100
```

### Status Colors
- **Green**: Test passed
- **Red**: Test failed
- **Yellow**: Test error
- **Gray**: Test skipped

## Troubleshooting

### Dashboard won't start
```bash
# Check port availability
netstat -an | grep 5001

# Use different port
python test_dashboard.py  # Edit port in file
```

### Tests not running
```bash
# Verify test files exist
ls test_*.py

# Check Python path
which python
python --version
```

### No results showing
```bash
# Run tests manually first
python test_evernothing.py
python test_s3.py
cd android && python test_android.py
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run tests and generate dashboard
  run: |
    python test_dashboard.py &
    sleep 5
    curl http://localhost:5001/dashboard > test_results.html
```

### Jenkins
```groovy
stage('Test Dashboard') {
    steps {
        sh 'python test_dashboard.py &'
        sh 'sleep 5'
        sh 'curl http://localhost:5001/dashboard > test_results.html'
    }
}
```

## Screenshots

### Dashboard View
- Summary cards with metrics
- Detailed test tables
- Comparison matrix

### Color Coding
- Black background
- Gold text
- Red borders and accents
- Green for pass
- Red for fail

## API Endpoints

### GET /dashboard
Returns full dashboard HTML

### GET /run_tests
Executes all tests and returns dashboard

### GET /
Landing page with link to dashboard

## Performance

- **Test Execution**: ~5-30 seconds depending on suite size
- **Dashboard Load**: <1 second
- **Refresh Rate**: Manual (click refresh)
- **Concurrent Users**: Supports multiple viewers

## Security Notes

- Dashboard runs on localhost by default
- No authentication required (local use)
- For production, add authentication
- Don't expose to public internet

## Future Enhancements

- [ ] Historical test results
- [ ] Test trend graphs
- [ ] Email notifications on failures
- [ ] Export results to JSON/CSV
- [ ] Real-time WebSocket updates
- [ ] Test coverage metrics
- [ ] Performance benchmarks
