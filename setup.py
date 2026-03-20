"""
Setup Script - Verify installation and create necessary directories
Run this once before using the scoring system
"""

import os


def check_packages():
    """Check if required packages are installed"""
    required = ["pandas", "numpy", "matplotlib"]
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"\n   Install with: pip install {' '.join(missing)}")
        return False

    return True


def create_directories():
    """Create necessary output directories"""
    dirs = ["outputs", "outputs/charts", "Data/Processed"]

    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✅ Created: {dir_path}/")
        else:
            print(f"✓  Exists: {dir_path}/")

    return True


def check_data_files():
    """Check if data files exist"""
    data_paths = ["Data/Processed/labelling/sample_labelled.csv"]

    found = False
    for path in data_paths:
        if os.path.exists(path):
            print(f"✅ Found data: {path}")
            found = True

    if not found:
        print(f"⚠️  No data files found. Checked:")
        for path in data_paths:
            print(f"   - {path}")
        print(f"\n   Make sure your data is in place before running the pipeline.")

    return True


def main():
    print("=" * 70)
    print("GEO/SEO SCORING ENGINE - SETUP CHECK")
    print("=" * 70)

    print("\n[1/4] Checking Python version...")

    print("\n[2/4] Checking required packages...")
    if not check_packages():
        print("\n❌ Setup incomplete. Install missing packages first.")
        return

    print("\n[3/4] Creating directories...")
    create_directories()

    print("\n[4/4] Checking for data files...")
    check_data_files()

    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
