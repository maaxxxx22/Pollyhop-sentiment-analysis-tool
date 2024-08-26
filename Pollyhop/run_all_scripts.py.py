import subprocess
import requests


def run_script(script_name):
    try:
        # Execute the script and capture the output
        result = subprocess.run(['python3', script_name], capture_output=True, text=True)

        # Check if the script executed successfully
        if result.returncode == 0:
            print(f"{script_name} executed successfully.\n")
            print(f"Output:\n{result.stdout}\n")
        else:
            print(f"Error in {script_name}:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"An error occurred while executing {script_name}: {str(e)}")
        return False
    return True


def main():
    # List of scripts to run in sequence
    scripts = ['fetch_bing_data.py', 'fetch_reddit_data.py', 'test4.py']

    for script in scripts:
        print(f"Running {script}...")
        if not run_script(script):
            print(f"Stopping execution due to an error in {script}.")
            break
        print(f"{script} completed.\n")


if __name__ == "__main__":
    main()
