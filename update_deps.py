import subprocess
import yaml
import sys
from datetime import datetime

def get_latest_version(package_name, date):
    """
    Get the latest version of a package from conda-forge as of a specific date.
    """
    try:
        result = subprocess.run(
            ['conda', 'search', package_name, '--channel', 'conda-forge', '--json'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Error searching for package {package_name}: {result.stderr}")
            return None

        import json
        package_data = json.loads(result.stdout)

        # Filter out versions that are newer than the specified date
        versions = []
        for pkg in package_data.get(package_name, []):
            timestamp = pkg['timestamp'] / 1000  # convert from ms to seconds
            build_date = datetime.utcfromtimestamp(timestamp).date()
            if build_date <= date:
                versions.append((pkg['version'], build_date))

        if versions:
            # Get the most recent version before or on the specified date
            latest_version = max(versions, key=lambda x: x[1])
            return latest_version[0]
        else:
            print(f"No version found for {package_name} before {date}")
            return None
    except Exception as e:
        print(f"Error fetching version for {package_name}: {e}")
        return None

def update_environment_yml(yml_file, date):
    """
    Reads an environment.yml file, looks for unpinned packages,
    and updates them with the latest version available as of the given date.
    """
    with open(yml_file, 'r') as file:
        env_data = yaml.safe_load(file)

    updated = False
    for i, dep in enumerate(env_data['dependencies']):
        # Skip pinned dependencies
        if isinstance(dep, str) and '=' not in dep:
            package_name = dep
            print(f"Finding version for unpinned package: {package_name}")
            version = get_latest_version(package_name, date)
            if version:
                print(f"Pinning {package_name} to version {version}")
                env_data['dependencies'][i] = f"{package_name}={version}"
                updated = True
        elif isinstance(dep, dict) and 'pip' in dep:
            print("Skipping pip dependencies for now.")

    # Save the updated environment.yml
    if updated:
        # create filename based on (basename)-updated.yml
        new_filename = yml_file.rsplit('.', 1)[0] + '-updated.yml'
        with open(new_filename, 'w') as new_file:
            yaml.dump(env_data, new_file, default_flow_style=False)
        print(f"Updated environment saved to {new_filename}")
    else:
        print("No unpinned packages found or no updates were made.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pin_env_versions.py <environment.yml> <YYYY-MM-DD>")
        sys.exit(1)

    yml_file = sys.argv[1]
    date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()

    update_environment_yml(yml_file, date)
