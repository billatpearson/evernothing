# EverNothing Android App

## Features
- Login/Register with Flask backend
- Browse folders and subfolders
- View notes in folders
- Create new folders and subfolders
- Add notes with key-value pairs
- Black/gold/red color scheme matching web UI
- Session management with backend

## Installation

**See [INSTALL.md](INSTALL.md) for complete step-by-step instructions.**

### Quick Start (Termux)
```bash
pkg update && pkg install python git
git clone https://github.com/yourusername/evernothing.git
cd evernothing/android
pip install -r requirements.txt
export EVERNOTHING_SERVER=http://127.0.0.1:5000
python main.py
```

### Desktop Testing
```bash
pip install -r requirements.txt
python main.py
```

## Configuration

Set the Flask backend URL via environment variable:
```bash
export EVERNOTHING_SERVER=http://your-server:5000
```

Default: `http://127.0.0.1:5000`

## Usage

1. **Login/Register**: Enter credentials on first screen
2. **Folders**: View all root folders, tap to open
3. **Folder Contents**: View notes and subfolders
4. **Add Note**: Tap "Add Note" button, enter note name and content
5. **Add Subfolder**: Tap "Add Subfolder" button, enter folder name
6. **Logout**: Tap "Logout" button on folders screen

## Architecture

- **APIClient**: HTTP communication with Flask backend
- **Screens**: Login, Register, Folders, Folder, AddFolder, AddNote
- **Session Management**: Cookies maintained by requests.Session
- **HTML Parsing**: Simple text parsing for folder/note lists

## Limitations

- No note editing (view only)
- No note deletion
- No folder deletion/rename
- No file attachments
- No search functionality
- No offline mode
- Basic HTML parsing (fragile)

## Testing

### Run Unit Tests
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python test_android.py -v

# Run specific test
python test_android.py AndroidAppTestCase.test_login_success
```

### Test Coverage
- API client authentication (login/register)
- Folder operations (list, create, navigate)
- Note operations (list, create)
- Network error handling
- HTML parsing edge cases
- Session persistence

### Integration Tests
Requires Flask backend running:
```bash
# Terminal 1: Start Flask
cd ..
python evernothing.py

# Terminal 2: Run tests
cd android
python test_android.py AndroidAppIntegrationTestCase
```

## Future Enhancements

- REST API endpoint in Flask for proper JSON responses
- Full CRUD operations for notes
- Offline sync with local SQLite
- File attachment support
- Search functionality
- Note history/rollback
