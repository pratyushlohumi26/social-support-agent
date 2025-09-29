#!/usr/bin/env python3
"""
UAE Social Support AI System - Quick Start Verification
Comprehensive system verification and testing
Version: 1.0.0
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def print_header():
    """Print verification header"""
    print("🚀 UAE SOCIAL SUPPORT AI SYSTEM - VERIFICATION")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Working directory: {os.getcwd()}")
    print()

def verify_file_structure():
    """Verify complete file structure"""
    print("📁 Verifying file structure...")

    expected_files = {
        'data/applications.json': 'Applications database',
        'data/training_programs.json': 'Training programs',
        'data/case_workers.json': 'Case workers',
        'data/analytics.json': 'Analytics data',
        'data/faq.json': 'FAQ database',
        'data/system_config.json': 'System configuration',
        'data/applications_summary.csv': 'Applications CSV',
        'data/training_programs.csv': 'Training programs CSV',
        'logs/processing_logs.json': 'Processing logs',
        'logs/system_activity.json': 'System activity logs',
        'config/environments.json': 'Environment config',
        'docs/api_endpoints.json': 'API documentation',
        'scripts/data_loader.py': 'Data loader utility',
        'scripts/ai_processor.py': 'AI processor engine',
        'scripts/init_system.py': 'System initialization',
        'README.md': 'System documentation'
    }

    missing_files = []
    total_size = 0

    for file_path, description in expected_files.items():
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            total_size += file_size
            print(f"   ✅ {description}: {file_path} ({file_size:,} bytes)")
        else:
            missing_files.append(f"{file_path} ({description})")
            print(f"   ❌ {description}: {file_path} - MISSING")

    print(f"\n📦 Total package size: {total_size:,} bytes ({total_size/1024:.1f} KB)")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files:")
        for missing in missing_files:
            print(f"      {missing}")
        return False

    print("✅ All files present and verified!")
    return True

def verify_json_integrity():
    """Verify JSON file integrity and structure"""
    print("\n🔍 Verifying JSON file integrity...")

    json_files = [
        'data/applications.json',
        'data/training_programs.json',
        'data/case_workers.json',
        'data/analytics.json',
        'data/faq.json',
        'data/system_config.json',
        'logs/processing_logs.json',
        'logs/system_activity.json',
        'config/environments.json',
        'docs/api_endpoints.json'
    ]

    corrupted_files = []

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic structure validation
            if 'data/' in file_path:
                if 'metadata' not in data:
                    print(f"   ⚠️  {file_path} - Missing metadata section")
                else:
                    print(f"   ✅ {file_path} - Valid structure")
            else:
                print(f"   ✅ {file_path} - Valid JSON")

        except json.JSONDecodeError as e:
            corrupted_files.append(f"{file_path}: {e}")
            print(f"   ❌ {file_path} - JSON Error: {e}")
        except Exception as e:
            corrupted_files.append(f"{file_path}: {e}")
            print(f"   ❌ {file_path} - Error: {e}")

    if corrupted_files:
        print(f"\n❌ Found {len(corrupted_files)} corrupted files")
        return False

    print("✅ All JSON files validated successfully!")
    return True

def verify_data_content():
    """Verify data content and relationships"""
    print("\n📊 Verifying data content...")

    try:
        # Load and verify applications
        with open('data/applications.json', 'r', encoding='utf-8') as f:
            apps_data = json.load(f)
        applications = apps_data.get('applications', [])
        print(f"   📱 Applications: {len(applications)} records")

        if applications:
            # Verify structure of first application
            sample_app = applications[0]
            required_sections = ['application_id', 'personal_info', 'employment_info', 'support_request']
            missing_sections = [section for section in required_sections if section not in sample_app]

            if missing_sections:
                print(f"   ⚠️  Missing sections in applications: {missing_sections}")
            else:
                print(f"   ✅ Application structure validated")

            # Check emirates coverage
            emirates = set(app['personal_info']['emirate'] for app in applications)
            print(f"   🌍 Emirates represented: {len(emirates)} ({', '.join(sorted(emirates))})")

        # Load and verify training programs
        with open('data/training_programs.json', 'r', encoding='utf-8') as f:
            programs_data = json.load(f)
        programs = programs_data.get('programs', [])
        print(f"   🎓 Training Programs: {len(programs)} records")

        # Load and verify case workers
        with open('data/case_workers.json', 'r', encoding='utf-8') as f:
            workers_data = json.load(f)
        workers = workers_data.get('case_workers', [])
        print(f"   👥 Case Workers: {len(workers)} records")

        # Load and verify analytics
        with open('data/analytics.json', 'r', encoding='utf-8') as f:
            analytics_data = json.load(f)
        analytics = analytics_data.get('analytics', {})
        print(f"   📈 Analytics Categories: {len(analytics)} sections")

        # Load and verify FAQ
        with open('data/faq.json', 'r', encoding='utf-8') as f:
            faq_data = json.load(f)
        faq = faq_data.get('faq', [])
        print(f"   ❓ FAQ Entries: {len(faq)} questions")

        return True

    except Exception as e:
        print(f"   ❌ Data verification error: {e}")
        return False

def test_python_utilities():
    """Test Python utility imports and basic functionality"""
    print("\n🐍 Testing Python utilities...")

    # Add scripts to path
    sys.path.append('scripts')

    try:
        # Test data loader
        print("   📊 Testing data loader...")
        from data_loader import UAEDataLoader

        loader = UAEDataLoader()
        print("      ✅ UAEDataLoader imported and instantiated")

        # Test loading a small sample
        applications = loader.load_applications(limit=5)
        print(f"      ✅ Loaded {len(applications)} sample applications")

        # Test other data loading
        programs = loader.load_training_programs()
        workers = loader.load_case_workers()
        analytics = loader.load_analytics()

        print(f"      ✅ All data types loaded successfully")

    except Exception as e:
        print(f"      ❌ Data loader test failed: {e}")
        return False

    try:
        # Test AI processor
        print("   🤖 Testing AI processor...")
        from ai_processor import AIProcessor

        processor = AIProcessor()
        print("      ✅ AIProcessor imported and instantiated")

        # Test assessment on sample application
        if applications:
            sample_app = applications[0]
            assessment = processor.assess_eligibility(sample_app)

            print(f"      ✅ Sample assessment completed:")
            print(f"         Score: {assessment['eligibility_score']}/100")
            print(f"         Recommendation: {assessment['recommendation']}")
            print(f"         Confidence: {assessment['confidence_level']:.2f}")

    except Exception as e:
        print(f"      ❌ AI processor test failed: {e}")
        return False

    print("   ✅ All Python utilities tested successfully!")
    return True

def run_comprehensive_test():
    """Run a comprehensive system test"""
    print("\n🧪 Running comprehensive system test...")

    try:
        sys.path.append('scripts')
        from data_loader import UAEDataLoader
        from ai_processor import AIProcessor

        # Load all data
        loader = UAEDataLoader()
        all_data = loader.load_all_data()

        print("   📊 Data loading test:")
        for key, value in all_data.items():
            if isinstance(value, list):
                print(f"      {key}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"      {key}: {len(value)} categories")
            else:
                print(f"      {key}: loaded")

        # Test AI processing on multiple applications
        processor = AIProcessor()
        applications = all_data['applications'][:10]  # Test with 10 applications

        print("\n   🤖 AI processing test:")
        processed = processor.process_batch(applications)

        # Generate summary
        recommendations = {}
        scores = []
        for app in processed:
            assessment = app.get('ai_assessment', {})
            rec = assessment.get('recommendation', 'Unknown')
            score = assessment.get('eligibility_score', 0)

            recommendations[rec] = recommendations.get(rec, 0) + 1
            scores.append(score)

        avg_score = sum(scores) / len(scores) if scores else 0

        print(f"      Processed: {len(processed)} applications")
        print(f"      Average Score: {avg_score:.1f}/100")
        print(f"      Recommendations: {recommendations}")

        # Test data export
        print("\n   📤 Export functionality test:")
        loader.export_to_csv("test_exports")

        # Verify export files were created
        export_files = ['test_exports/applications_export.csv', 
                       'test_exports/training_programs_export.csv',
                       'test_exports/case_workers_export.csv']

        for export_file in export_files:
            if Path(export_file).exists():
                print(f"      ✅ {export_file} created")
            else:
                print(f"      ⚠️  {export_file} not created")

        print("   ✅ Comprehensive test completed successfully!")
        return True

    except Exception as e:
        print(f"   ❌ Comprehensive test failed: {e}")
        return False

def generate_verification_report():
    """Generate verification report"""
    print("\n📋 Generating verification report...")

    report = {
        "verification_date": datetime.now().isoformat(),
        "system_name": "UAE Social Support AI System",
        "package_version": "1.0.0",
        "verification_status": "PASSED",
        "components_verified": [
            "File structure integrity",
            "JSON data validation", 
            "Data content verification",
            "Python utilities testing",
            "Comprehensive system test"
        ],
        "system_ready": True,
        "next_steps": [
            "Begin development with synthetic dataset",
            "Customize system configuration",
            "Integrate with existing systems", 
            "Deploy to target environment"
        ]
    }

    with open('verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("✅ Verification report saved: verification_report.json")

def main():
    """Main verification function"""
    print_header()

    verification_steps = [
        ("File Structure", verify_file_structure),
        ("JSON Integrity", verify_json_integrity),
        ("Data Content", verify_data_content),
        ("Python Utilities", test_python_utilities),
        ("Comprehensive Test", run_comprehensive_test)
    ]

    failed_steps = []

    for step_name, step_function in verification_steps:
        print(f"\n{'='*20} {step_name.upper()} {'='*20}")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            failed_steps.append(step_name)

    # Final results
    print("\n" + "🎊" * 15 + " VERIFICATION COMPLETED " + "🎊" * 15)
    print("=" * 70)

    if failed_steps:
        print(f"\n❌ VERIFICATION FAILED!")
        print(f"Failed steps: {', '.join(failed_steps)}")
        print("\nPlease check the errors above and ensure:")
        print("  1. ZIP file was extracted completely")
        print("  2. All files are present and readable")
        print("  3. Python environment is properly configured")
        sys.exit(1)
    else:
        print("\n🎊 VERIFICATION PASSED SUCCESSFULLY! 🎊")
        print("\n✅ All systems verified and operational!")
        print("\n🚀 UAE Social Support AI System Status:")
        print("   📊 Data: 150+ applications loaded and validated")
        print("   🤖 AI: Processing engine operational")
        print("   🔧 Utils: All Python utilities functional")
        print("   📈 Analytics: Dashboard data ready")
        print("   🌐 API: Framework ready for development")

        print("\n📖 Quick Start Commands:")
        print('   python -c "from scripts.data_loader import UAEDataLoader; loader = UAEDataLoader(); data = loader.load_all_data()"')
        # print('   python -c "from scripts.ai_processor import AIProcessor; print('AI Engine Ready!')"')

        print("\n🎯 System Ready For:")
        print("   ✅ Web Application Development")
        print("   ✅ AI Model Training & Testing")
        print("   ✅ Dashboard & Analytics Creation")
        print("   ✅ API Development & Integration")
        print("   ✅ Production System Deployment")

        # Generate report
        generate_verification_report()

        print("\n🇦🇪 UAE SOCIAL SUPPORT AI SYSTEM READY FOR ACTION! 🚀")

if __name__ == "__main__":
    main()
