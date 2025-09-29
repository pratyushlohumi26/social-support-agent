#!/usr/bin/env python3
"""
UAE Social Support AI System - Data Loader Utility
Complete data management and loading system
Version: 1.0.0
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class UAEDataLoader:
    """Comprehensive data loader for UAE Social Support AI System"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.applications = None
        self.training_programs = None
        self.case_workers = None
        self.analytics = None
        self.faq = None
        self.system_config = None

        # Verify data directory exists
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory '{data_dir}' not found. Please ensure ZIP was extracted properly.")

    def load_applications(self, limit: Optional[int] = None) -> List[Dict]:
        """Load application data from JSON file"""
        file_path = self.data_dir / "applications.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Applications file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in applications file: {e}")

        applications = data.get('applications', [])
        if limit:
            applications = applications[:limit]

        self.applications = applications
        print(f"✅ Loaded {len(applications)} applications")
        return applications

    def load_training_programs(self) -> List[Dict]:
        """Load training programs data"""
        file_path = self.data_dir / "training_programs.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Training programs file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        programs = data.get('programs', [])
        self.training_programs = programs
        print(f"✅ Loaded {len(programs)} training programs")
        return programs

    def load_case_workers(self) -> List[Dict]:
        """Load case workers data"""
        file_path = self.data_dir / "case_workers.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Case workers file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        workers = data.get('case_workers', [])
        self.case_workers = workers
        print(f"✅ Loaded {len(workers)} case workers")
        return workers

    def load_analytics(self) -> Dict:
        """Load analytics and reporting data"""
        file_path = self.data_dir / "analytics.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Analytics file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        analytics = data.get('analytics', {})
        self.analytics = analytics
        print("✅ Loaded analytics data")
        return analytics

    def load_faq(self) -> List[Dict]:
        """Load FAQ data"""
        file_path = self.data_dir / "faq.json"

        if not file_path.exists():
            raise FileNotFoundError(f"FAQ file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        faq_items = data.get('faq', [])
        self.faq = faq_items
        print(f"✅ Loaded {len(faq_items)} FAQ entries")
        return faq_items

    def load_system_config(self) -> Dict:
        """Load system configuration"""
        file_path = self.data_dir / "system_config.json"

        if not file_path.exists():
            raise FileNotFoundError(f"System config file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.system_config = config
        print("✅ Loaded system configuration")
        return config

    def load_all_data(self) -> Dict:
        """Load all data sources at once"""
        print("🔄 Loading all UAE Social Support AI data...")
        print("=" * 50)

        try:
            data = {
                'applications': self.load_applications(),
                'training_programs': self.load_training_programs(),
                'case_workers': self.load_case_workers(),
                'analytics': self.load_analytics(),
                'faq': self.load_faq(),
                'system_config': self.load_system_config()
            }

            print(f"\n🎊 All data loaded successfully!")
            print(f"📊 {len(data['applications'])} applications")
            print(f"🎓 {len(data['training_programs'])} training programs")
            print(f"👥 {len(data['case_workers'])} case workers")
            print(f"❓ {len(data['faq'])} FAQ entries")
            print(f"📈 Analytics data included")
            print(f"⚙️ System configuration loaded")

            return data

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise

    def get_applications_by_status(self, status: str) -> List[Dict]:
        """Get applications filtered by processing status"""
        if not self.applications:
            self.load_applications()

        filtered = [app for app in self.applications 
                   if app.get('processing_status', '').lower() == status.lower()]
        return filtered

    def get_applications_by_emirate(self, emirate: str) -> List[Dict]:
        """Get applications filtered by emirate"""
        if not self.applications:
            self.load_applications()

        filtered = [app for app in self.applications 
                   if app.get('personal_info', {}).get('emirate', '').lower() == emirate.lower()]
        return filtered

    def get_applications_by_support_type(self, support_type: str) -> List[Dict]:
        """Get applications filtered by support type"""
        if not self.applications:
            self.load_applications()

        filtered = [app for app in self.applications 
                   if app.get('support_request', {}).get('support_type', '').lower() == support_type.lower()]
        return filtered

    def get_applications_summary_df(self) -> pd.DataFrame:
        """Get applications as pandas DataFrame for analysis"""
        if not self.applications:
            self.load_applications()

        # Create summary DataFrame
        summary_data = []
        for app in self.applications:
            personal = app.get('personal_info', {})
            employment = app.get('employment_info', {})
            support = app.get('support_request', {})

            summary_data.append({
                'application_id': app.get('application_id'),
                'submission_date': app.get('submission_date'),
                'full_name': personal.get('full_name'),
                'nationality': personal.get('nationality'),
                'emirate': personal.get('emirate'),
                'family_size': personal.get('family_size'),
                'dependents': personal.get('dependents'),
                'employment_status': employment.get('employment_status'),
                'monthly_salary': employment.get('monthly_salary', 0),
                'support_type': support.get('support_type'),
                'urgency_level': support.get('urgency_level'),
                'amount_requested': support.get('amount_requested', 0),
                'processing_status': app.get('processing_status'),
                'case_worker_id': app.get('case_worker_id')
            })

        return pd.DataFrame(summary_data)

    def export_to_csv(self, output_dir: str = "exports"):
        """Export all data to CSV files"""
        export_path = Path(output_dir)
        export_path.mkdir(exist_ok=True)

        # Export applications summary
        if self.applications:
            df = self.get_applications_summary_df()
            df.to_csv(export_path / "applications_export.csv", index=False)
            print(f"📄 Exported applications to {export_path}/applications_export.csv")

        # Export training programs
        if self.training_programs:
            programs_df = pd.DataFrame(self.training_programs)
            programs_df.to_csv(export_path / "training_programs_export.csv", index=False)
            print(f"📄 Exported training programs to {export_path}/training_programs_export.csv")

        # Export case workers
        if self.case_workers:
            workers_df = pd.DataFrame(self.case_workers)
            workers_df.to_csv(export_path / "case_workers_export.csv", index=False)
            print(f"📄 Exported case workers to {export_path}/case_workers_export.csv")

        print("✅ Export completed!")

    def get_statistics(self) -> Dict:
        """Get comprehensive system statistics"""
        if not self.applications:
            self.load_applications()

        stats = {}

        # Application statistics
        stats['applications'] = {
            'total': len(self.applications),
            'by_status': {},
            'by_emirate': {},
            'by_support_type': {},
            'by_urgency': {}
        }

        for app in self.applications:
            # Status distribution
            status = app.get('processing_status', 'Unknown')
            stats['applications']['by_status'][status] = stats['applications']['by_status'].get(status, 0) + 1

            # Emirate distribution
            emirate = app.get('personal_info', {}).get('emirate', 'Unknown')
            stats['applications']['by_emirate'][emirate] = stats['applications']['by_emirate'].get(emirate, 0) + 1

            # Support type distribution
            support_type = app.get('support_request', {}).get('support_type', 'Unknown')
            stats['applications']['by_support_type'][support_type] = stats['applications']['by_support_type'].get(support_type, 0) + 1

            # Urgency distribution
            urgency = app.get('support_request', {}).get('urgency_level', 'Unknown')
            stats['applications']['by_urgency'][urgency] = stats['applications']['by_urgency'].get(urgency, 0) + 1

        # Calculate approval rate
        approved_count = stats['applications']['by_status'].get('Approved', 0)
        stats['applications']['approval_rate'] = (approved_count / len(self.applications) * 100) if self.applications else 0

        return stats


if __name__ == "__main__":
    # Example usage and testing
    try:
        loader = UAEDataLoader()

        # Load all data
        all_data = loader.load_all_data()

        # Get some analytics
        print(f"\n📊 Quick Analytics:")

        approved_apps = loader.get_applications_by_status("Approved")
        print(f"✅ Approved applications: {len(approved_apps)}")

        dubai_apps = loader.get_applications_by_emirate("dubai")
        print(f"🏙️ Dubai applications: {len(dubai_apps)}")

        emergency_apps = loader.get_applications_by_support_type("emergency_support")
        print(f"🚨 Emergency support requests: {len(emergency_apps)}")

        # Get comprehensive statistics
        stats = loader.get_statistics()
        print(f"\n📈 System Statistics:")
        print(f"   Total Applications: {stats['applications']['total']}")
        print(f"   Approval Rate: {stats['applications']['approval_rate']:.1f}%")

        # Export to CSV
        loader.export_to_csv()

    except Exception as e:
        print(f"❌ Error in data loader demo: {e}")
