# Smart Weight Bridge Management System

A comprehensive weighing bridge management system designed for manganese mining companies, featuring Smart Weight machine integration and dual-user access for administrators and operators.

## Features

### Administrator Dashboard
- **User Management**: Register, activate/deactivate operators and administrators
- **Truck Management**: Register trucks and assign multiple drivers
- **Database View**: Complete access to all weighing records
- **Advanced Search**: Filter by any database column with dropdown selection
- **Edit Capability**: Correct errors and ensure data integrity
- **Excel Export**: Generate filtered or complete reports in Excel format
- **Real-time Statistics**: Track total records, weights, and system status

### Operator Dashboard
- **Smart Weight Integration**: Real-time connection to weighing bridge
- **Automatic Weight Calculation**: Initial and final weights with net load calculation
- **Material Selection**: HGL, LGL, HGLogs, LGLogs, HGF, LGF dropdown
- **Product Selection**: LNG 24, LNG 25, LNG 26.5 dropdown
- **Ticket Generation**: Automatic weighing ticket creation and printing
- **Live Weight Display**: Real-time weight readings with stability indicators

### Technical Features
- **Offline/Online Capability**: Works in both modes with data synchronization
- **Smart Weight Machine Integration**: Full compatibility with Smart Weight specifications
- **Data Integrity**: Unique constraints on Registration, Waybill, and Transporter Name
- **Role-based Access**: Separate permissions for administrators and operators
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Installation

### Prerequisites
- Python 3.11 or higher
- SQLite database (included)
- Smart Weight weighing bridge machine

### Setup Steps

1. **Clone or Download the Project**
   ```bash
   # Extract the project files to your desired directory
   cd weighing-bridge-system
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Initialization**
   ```bash
   python app.py
   ```
   The system will automatically create and initialize the database with default data.

4. **Access the System**
   - Open your web browser and navigate to: `http://localhost:8050`
   - Default administrator credentials:
     - Username: `admin`
     - Password: `admin123`

## Configuration

### Smart Weight Machine Settings
Access the system settings to configure:
- Communication port (default: COM1)
- Baud rate (default: 9600)
- Auto-zero interval
- Tare timeout

### Database Settings
The system uses SQLite by default. All database files are stored in:
- Main database: `weighing_bridge.db`
- Logs and backups: Created automatically

## User Guide

### Administrator Functions

1. **User Management**
   - Navigate to Admin → Users
   - Click "Register User" to add new operators
   - Use edit/delete buttons to manage existing users
   - Toggle active/inactive status as needed

2. **Truck Registration**
   - Navigate to Admin → Trucks
   - Register trucks with unique registration numbers
   - Assign multiple drivers to each truck
   - Set transporter names and company details

3. **Records Management**
   - View all weighing records in the Records section
   - Use search and filter functionality
   - Edit records to correct errors
   - Export filtered data to Excel

4. **Reports**
   - Generate comprehensive reports with date ranges
   - Filter by any column (registration, transporter, etc.)
   - Export to Excel for analysis
   - View visual analytics and charts

### Operator Functions

1. **Weighing Operations**
   - Connect to Smart Weight machine
   - Capture initial weight (empty truck)
   - Capture final weight (loaded truck)
   - System automatically calculates net load

2. **Data Entry**
   - Enter required information (waybill, truck details, etc.)
   - Select material and product from dropdowns
   - Choose operator and loader
   - Save record to generate automatic ticket

3. **Ticket Generation**
   - System automatically generates weighing tickets
   - Print tickets for drivers and records
   - Tickets include all weighing details and company information

## Database Schema

### Primary Tables
- **users**: Authentication and role management
- **trucks**: Truck registration with unique constraints
- **drivers**: Driver information and assignments
- **weighing_records**: Main weighing data with all required fields
- **materials**: Manganese material types (HGL, LGL, etc.)
- **products**: LNG specifications (24, 25, 26.5)

### Unique Constraints
- Truck registration numbers
- Waybill numbers
- Transporter names

## Smart Weight Integration

The system integrates directly with Smart Weight weighing machines:
- Real-time weight readings
- Stability indicators
- Tare and zero functions
- Automatic weight capture
- Connection status monitoring

## Data Export

### Excel Export Features
- Filtered data export
- All columns included
- Formatted with proper headers
- Automatic file naming with timestamps
- Compatible with Microsoft Excel and LibreOffice

## Security Features

- Role-based access control
- Password encryption
- Session management
- Activity logging
- Data validation

## Offline Mode

The system supports offline operations:
- Local data storage
- Automatic synchronization when online
- No data loss during connectivity issues
- Queue management for pending syncs

## Troubleshooting

### Common Issues

1. **Smart Weight Connection Failed**
   - Check cable connections
   - Verify port settings in system configuration
   - Ensure machine is powered on

2. **Database Errors**
   - Restart the application
   - Check disk space
   - Verify database file permissions

3. **Login Issues**
   - Verify username and password
   - Check if user account is active
   - Contact administrator if needed

### Support

For technical support and troubleshooting:
1. Check system logs
2. Verify Smart Weight machine connection
3. Ensure all dependencies are installed
4. Contact system administrator

## System Requirements

### Minimum Requirements
- Python 3.11
- 2GB RAM
- 500MB disk space
- Network connection for online features

### Recommended Requirements
- Python 3.11 or higher
- 4GB RAM
- 2GB disk space
- Stable internet connection
- Modern web browser (Chrome, Firefox, Safari, Edge)

## License

This system is developed for Manganese Mining Company operations.
© 2024 Manganese Mining Company - All rights reserved.

## Version History

### Version 1.0.0
- Initial release with full Smart Weight integration
- Complete admin and operator dashboards
- Offline/online capability
- Excel export functionality
- Material and product management for manganese mining

---

**Note**: This system is specifically designed for manganese mining operations with Smart Weight weighing bridge machines. Ensure proper training for all users before deployment.