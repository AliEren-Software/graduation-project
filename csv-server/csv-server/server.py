import time
import traceback

from csv_server import create_app


app = create_app()


if __name__ == "__main__":
    while True:
        try:
            app.run(host="0.0.0.0", port=5000, use_reloader=False)
            break
        except KeyboardInterrupt:
            print("Server stopped by user.")
            break
        except Exception:
            print("Server crashed unexpectedly. Restarting in 5 seconds...")
            traceback.print_exc()
            time.sleep(5)
