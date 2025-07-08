import subprocess
import threading
import os
import time

class SnortWrapper:
    def __init__(self, snort_conf_path="/etc/snort/snort.conf", alert_log_path="/var/log/snort/alert"):
        self.snort_conf_path = snort_conf_path
        self.alert_log_path = alert_log_path
        self.snort_process = None
        self.log_tail_process = None
        self.log_thread = None
        self.running = False

    def _tail_log(self):
        print(f"Tailing Snort alert log: {self.alert_log_path}")
        # Ensure the log file exists before tailing
        if not os.path.exists(self.alert_log_path):
            print(f"Warning: Snort alert log file not found at {self.alert_log_path}. Waiting for it to be created...")
            # Wait for the file to be created by Snort
            while not os.path.exists(self.alert_log_path) and self.running:
                time.sleep(1)
            if not self.running: # If stopped while waiting
                return

        try:
            self.log_tail_process = subprocess.Popen(
                ["tail", "-F", self.alert_log_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            for line in iter(self.log_tail_process.stdout.readline, ''):
                if not self.running: # Check if we should stop
                    break
                print(f"Snort Alert: {line.strip()}")
                # Here you would typically send the line to the log_parser
                # from ..utils.log_parser import parse_snort_log
                # parsed_data = parse_snort_log(line.strip())
                # if parsed_data:
                #     # Send to ML model or save to DB
                #     pass
        except Exception as e:
            print(f"Error tailing Snort log: {e}")
        finally:
            if self.log_tail_process and self.log_tail_process.poll() is None:
                self.log_tail_process.terminate()
                self.log_tail_process.wait()

    def start_snort(self):
        if self.running:
            print("Snort is already running.")
            return

        print("Starting Snort...")
        try:
            # Snort command to run in IDS mode, log to /var/log/snort, and output full alerts
            # We run it in the background and then tail the log file
            self.snort_process = subprocess.Popen(
                ["snort", "-c", self.snort_conf_path, "-i", "eth0", "-A", "full", "-l", "/var/log/snort"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"Snort started with PID: {self.snort_process.pid}")
            self.running = True
            self.log_thread = threading.Thread(target=self._tail_log)
            self.log_thread.daemon = True # Allow main program to exit even if thread is running
            self.log_thread.start()

        except FileNotFoundError:
            print("Error: Snort command not found. Make sure Snort is installed and in your PATH.")
        except Exception as e:
            print(f"Error starting Snort: {e}")

    def stop_snort(self):
        if not self.running:
            print("Snort is not running.")
            return

        print("Stopping Snort...")
        self.running = False
        if self.log_tail_process and self.log_tail_process.poll() is None:
            self.log_tail_process.terminate()
            self.log_tail_process.wait()
        if self.snort_process and self.snort_process.poll() is None:
            self.snort_process.terminate()
            self.snort_process.wait()
        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=5) # Give thread some time to finish
        print("Snort stopped.")

if __name__ == "__main__":
    # This part is for testing the SnortWrapper independently
    # In a real scenario, this would be managed by the FastAPI app startup
    snort_wrapper = SnortWrapper()
    snort_wrapper.start_snort()
    try:
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        snort_wrapper.stop_snort()
