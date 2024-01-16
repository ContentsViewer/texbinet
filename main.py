from fastapi import FastAPI
import uvicorn
import argparse

from texbinet.watchdog import Watchdog

app = FastAPI()


@app.post("/watchdog")
def post_watchdog():
    return {"message": "Hello World"}


if __name__ == "__main__":
    watchdog = Watchdog()

    parser = argparse.ArgumentParser(
        description="SSR host server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Bind socket to this host."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind socket to this port. If 0, an available port will be picked.",
    )

    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)

    watchdog.stop()
    watchdog.join()
