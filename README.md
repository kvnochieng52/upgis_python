# UPG Management Information System

A comprehensive Management Information System for Village Enterprise's Ultra-Poor Graduation (UPG) program, designed to track households, business groups, savings groups, training, and program outcomes.

## 🎯 System Overview

This system implements the complete UPG 12-month graduation model with:
- **15 Core Data Models** based on the Graduation Tracking System
- **7 User Roles** with role-based access control
- **Mobile Data Collection** integration with KoboToolbox
- **Comprehensive Dashboards** for program monitoring
- **Advanced Reporting** and analytics
- **Complete Workflow Management** from targeting to graduation

## 📋 Features

### Core Modules
- **Households Management** - Registration, eligibility, PPI scoring, tracking
- **Business Groups** - Formation, grant management (SB/PR grants), progress monitoring
- **Business Savings Groups (BSG)** - Member management, savings tracking
- **Training & Mentoring** - Module management, attendance tracking, visit documentation
- **Survey Management** - Mobile data collection, KoboToolbox integration
- **Reports & Analytics** - Custom reports, dashboards, data visualization

### User Roles & Permissions
1. **County Executive** - High-level program overview and reports
2. **County Assembly** - Ward-specific data and progress monitoring
3. **ICT Administrator** - Full system access and user management
4. **M&E Staff** - Complete data access, survey creation, reporting
5. **CCO & Director** - Program management and oversight
6. **Mentor Supervisor** - Village management, mentor oversight
7. **Mentor** - Household registration, data collection, field activities

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download** the UPG_System folder to your laptop

2. **Open Command Prompt** and navigate to the system directory:
   ```bash
   cd "C:\path\to\UPG_System"
   ```

3. **Run the automated setup**:
   ```bash
   python setup.py
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

5. **Open your browser** and go to: http://127.0.0.1:8000

### Manual Setup (if automated setup fails)

1. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

4. **Start server**:
   ```bash
   python manage.py runserver
   ```

## 📊 System Architecture

### Database Schema
The system implements the complete Graduation Model with these core entities:
- **Mentor** - Business mentor contact information
- **BusinessMentorCycle** - Mentor cycle and activities tracking
- **Village** - Geographic and administrative information
- **Household** - Beneficiary demographic and contact details
- **PPI** - Poverty Probability Index scoring
- **HouseholdSurvey** - Living conditions and assets
- **BusinessGroup** - Joint business ventures (2-3 entrepreneurs)
- **SBGrant & PRGrant** - Seed and performance-based grants
- **BusinessSavingsGroup** - Community savings management
- **Training & TrainingAttendance** - Capacity building tracking
- **MentoringVisit** - Mentor support documentation

### Technology Stack
- **Backend**: Django 4.2 (Python web framework)
- **Database**: SQLite (for development), PostgreSQL/MySQL (for production)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Authentication**: Django built-in with custom user model
- **Reports**: Django templates, PDF generation
- **Mobile Support**: Responsive design, offline capability

## 🔧 Configuration

### User Management
1. Login to admin panel: http://127.0.0.1:8000/admin
2. Create users with appropriate roles
3. Assign villages to mentors through user profiles

### System Settings
- Configure countries, offices, and administrative units
- Set up program cycles (e.g., FY25C1, FY25C2)
- Define business types and grant amounts
- Customize training modules

### Data Import
- Import ESR lists for household targeting
- Bulk import village and administrative data
- Configure KoboToolbox integration endpoints

## 📱 Mobile Integration

The system supports mobile data collection through:
- **Responsive Design** - Works on smartphones and tablets
- **Offline Capability** - Data entry without internet connection
- **KoboToolbox Integration** - Seamless survey data sync
- **GPS Capture** - Location data for households and activities

### Key Survey Forms Supported:
- Household Eligibility Assessment
- BSG Registration
- Business Progress Surveys
- Training Attendance
- PPI Scoring

## 📈 Reporting & Analytics

### Dashboard Features
- **Role-based Views** - Each user sees relevant data only
- **Real-time Statistics** - Program progress, enrollment, graduation rates
- **Geographic Coverage** - Village-level program saturation
- **Financial Tracking** - Grant disbursement, business performance

### Custom Reports
- Household graduation pipeline
- Business group performance analysis
- Savings group financial reports
- Training effectiveness metrics
- Mentor performance tracking
- County-level program summaries

## 🔒 Security Features

- **Role-based Access Control** - Granular permissions by user type
- **Audit Logging** - Complete activity tracking
- **Data Encryption** - Secure data storage and transmission
- **Session Management** - Automatic timeout and security
- **Multi-factor Authentication** - Optional 2FA/MFA support

## 📖 User Guide

### For Mentors
1. **Login** with your assigned credentials
2. **View Dashboard** to see your assigned villages and households
3. **Register Households** using eligibility assessment
4. **Conduct Surveys** through mobile interface
5. **Track Training** attendance and progress
6. **Monitor Business Groups** and savings activities

### For M&E Staff
1. **Create Surveys** using form builder
2. **Assign Tasks** to mentors and supervisors
3. **Monitor Data Quality** through validation reports
4. **Generate Reports** for program management
5. **Export Data** for external analysis

### For County Officials
1. **View Program Overview** on dashboard
2. **Access Summary Reports** by ward/constituency
3. **Monitor Budget Utilization** and grant disbursement
4. **Track Graduation Outcomes** and impact metrics

## 🛠 Troubleshooting

### Common Issues

**Database Connection Error**
- Ensure SQLite database file has write permissions
- Check DJANGO_SETTINGS_MODULE environment variable

**Missing Dependencies**
- Run: `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed

**Login Issues**
- Create superuser: `python manage.py createsuperuser`
- Check user role assignments in admin panel

**Survey Data Sync**
- Verify internet connection
- Check KoboToolbox API credentials
- Review data validation rules

## 📞 Support

For technical support and questions:
- Check the troubleshooting section above
- Review Django documentation: https://docs.djangoproject.com/
- Contact system administrator for user access issues

## 📄 License

This system is developed for Village Enterprise's Ultra-Poor Graduation program implementation.

---

**Version**: 1.0.0
**Last Updated**: 2024
**Developed for**: Village Enterprise - Ultra-Poor Graduation Program