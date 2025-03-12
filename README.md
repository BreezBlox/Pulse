# Pulse - Production Job Tracking System

Pulse is a comprehensive production job tracking system for manufacturing environments, enabling real-time monitoring, time tracking, and operational management.

## Key Features

- Real-time job status and performance tracking
- Component management and validation
- Benchmark database with Excel upload and synchronization
- Automated PDF generation for operator checklists and sales forms
- Gamified component selection interface
- Comprehensive reporting and analytics

## Technology Stack

- **Backend**: Flask web framework
- **Database**: PostgreSQL
- **Frontend**: Bootstrap with responsive design
- **PDF Generation**: ReportLab and WeasyPrint

## Getting Started

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your PostgreSQL database
4. Run the application: `gunicorn --bind 0.0.0.0:5000 main:app`