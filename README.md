# Remote Control App

A cross-platform remote-control solution that lets you manage a Linux desktop from any device via a web interface.

## Features

* **System Monitoring**: Real-time CPU, memory, and disk usage statistics
* **File Management**: Browse and open files with system default applications
* **Process Control**: View, search, and terminate running processes
* **Application Management**: List and launch installed applications
* **Real-time Updates**: Automatic refresh of system information and process lists
* **Responsive Design**: Works on desktop and mobile devices

## Architecture

```
+-------------+          HTTP          +-----------+         System Calls         +-------------+
|             | <--------------------> |  Django   | <--------------------------> |   Linux     |
| Next.js UI  |                       | Backend   |                             | System      |
| (Browser)   |                       |           |                             |             |
+-------------+                       +-----------+                             +-------------+
```

### Backend Components

1. **Django API Endpoints**:
   - `/api/system-info/` - System statistics
   - `/api/list-directory/` - Directory contents
   - `/api/open-file/` - File operations
   - `/api/open-app/` - Application launch
   - `/api/running-processes/` - Process list
   - `/api/kill-process/` - Process termination

2. **System Agent** (`agent.py`):
   - System information via `psutil`
   - File operations via `os` module
   - Process management
   - Application launching via `subprocess`

### Frontend Components

1. **SystemInfo**:
   - Real-time system statistics
   - Auto-updates every 5 seconds
   - CPU, memory, and disk usage display

2. **FileExplorer**:
   - Directory navigation
   - File/folder listings
   - File size and modification time
   - Open files with default applications

3. **ProcessManager**:
   - List all running processes
   - Process search and filtering
   - Process termination
   - Auto-refresh functionality

4. **AppLauncher**:
   - List installed applications
   - Application search
   - One-click app launching
   - Command information display

## How It Works

### System Information Flow
```
1. Frontend requests system info every 5s
2. Backend uses psutil to gather stats
3. Data sent back as JSON
4. UI updates with new information
```

### File Operations Flow
```
1. User navigates directories in UI
2. Backend lists directory contents
3. User clicks file to open
4. Backend uses xdg-open
5. File opens in default application
```

### Process Management Flow
```
1. Frontend fetches process list
2. Backend uses psutil to get processes
3. User can search and filter processes
4. Termination requests sent to backend
5. Backend terminates specified process
```

### Application Launch Flow
```
1. Backend scans application directories
2. Frontend displays available apps
3. User clicks to launch app
4. Backend executes app via subprocess
```

## Prerequisites

* Python 3.10+
* Node.js 18+
* npm or yarn
* Linux system with `xdg-open` installed
* Required Python packages:
  - Django
  - django-cors-headers
  - psutil
  - python-xlib

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd remote-control
   ```

2. Backend Setup:
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```

3. Frontend Setup:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Access the web interface at `http://localhost:3000`

## Usage

### System Information
- View real-time system statistics
- Monitor CPU, memory, and disk usage
- Auto-updates every 5 seconds

### File Management
- Navigate through directory structure
- View file details (size, modified date)
- Open files with default applications
- Navigate up/down directory tree

### Process Management
- View all running processes
- Search by process name, PID, or user
- Monitor process memory usage
- Terminate processes safely

### Application Management
- Browse installed applications
- Search application catalog
- View application commands
- Launch applications remotely

## Security Considerations

* **CORS**: Currently allows all origins (development only)
* **Authentication**: Implement before production use
* **Process Control**: Restrict process termination rights
* **File Access**: Implement proper file access controls
* **API Security**: Add rate limiting and request validation

## Development

### Backend Structure
```
backend/
├── control_app/
│   ├── agent.py     # System interaction
│   ├── views.py     # API endpoints
│   └── urls.py      # URL routing
└── config/
    └── settings.py  # Django settings
```

### Frontend Structure
```
frontend/
├── app/
│   ├── components/
│   │   ├── SystemInfo.tsx
│   │   ├── FileExplorer.tsx
│   │   ├── ProcessManager.tsx
│   │   └── AppLauncher.tsx
│   └── page.tsx
└── package.json
```

## Production Deployment

1. Configure CORS for specific origins
2. Implement authentication system
3. Set up HTTPS with SSL certificates
4. Use Gunicorn for Django deployment
5. Configure proper process permissions
6. Implement rate limiting
7. Add monitoring and logging

## Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure proper system permissions
2. **CORS Errors**: Check CORS configuration
3. **Process Control**: Verify user permissions
4. **File Access**: Check file system permissions

### Debug Tips
- Check Django logs for backend issues
- Monitor browser console for frontend errors
- Verify system permissions
- Test file system access rights

## License

MIT # ShellSync
# ShellSync
