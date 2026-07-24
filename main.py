import argparse
import sys
from vision import vision_loop
from drone_thread import DroneWorkerThread


def main():
    parser = argparse.ArgumentParser(description="CoDrone Edu Vision Controller")
    parser.add_argument("--mock-drone", action="store_true", default=False,
                        help="Run system in dry-run simulation mode without connecting physical Bluetooth hardware.")
    parser.add_argument("--mock-camera", action="store_true", default=False,
                        help="Run vision loop in mock mode without requesting webcam hardware.")
    parser.add_argument("--flight-log", "--flight_log", "--fight_log", "--fight-log", dest="flight_log", action="store_true", default=False,
                        help="Enable flight monitoring logger mode to capture hand orientation, resultant inputs, and live sensor data into CSV logs.")

    args = parser.parse_args()

    print("==================================================")
    print("      CoDrone Edu Vision Controller Starting      ")
    print("==================================================")
    print(f"[*] Hardware Mode: {'MOCK DRONE (DRY-RUN)' if args.mock_drone else 'PHYSICAL BLUETOOTH DRONE'}")
    print(f"[*] Monitoring Mode: {'ENABLED (LOGGING LIVE TELEMETRY)' if args.flight_log else 'DISABLED'}")

    worker = DroneWorkerThread(mock_drone=args.mock_drone, tick_rate_hz=20.0)
    worker.start()

    try:
        vision_loop(mock_camera=args.mock_camera, enable_flight_log=args.flight_log)
    except KeyboardInterrupt:
        print("\n[*] Keyboard Interrupt received. Exiting...")
    finally:
        worker.stop()
        print("[+] Controller application shutdown complete.")


if __name__ == "__main__":
    main()
