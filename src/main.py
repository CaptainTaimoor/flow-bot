import os
import json
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from src.config.settings import settings
from src.database.db import init_db, get_connection
from src.jobs.queue import JobQueue
from src.models.domain import JobCreate
from src.jobs.runner import JobRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            try:
                with open("src/api/dashboard.html", "rb") as f:
                    self.wfile.write(f.read())
            except Exception:
                self.wfile.write(b"<h1>Dashboard HTML missing</h1>")
                
        elif parsed.path == "/api/v1/jobs":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            conn = get_connection()
            queue = JobQueue(conn)
            jobs = queue.get_all_jobs()
            conn.close()
            
            out = []
            for j in jobs:
                out.append({
                    "id": j.id, "prompt": j.prompt, "status": j.status, 
                    "created_at": str(j.created_at), "output_path": j.output_path, 
                    "error_message": j.error_message
                })
            self.wfile.write(json.dumps(out).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/v1/jobs":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            conn = get_connection()
            queue = JobQueue(conn)
            job = queue.add_job(JobCreate(prompt=data.get("prompt", "")))
            conn.close()
            
            self.send_response(201)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": job.id, "prompt": job.prompt, "status": job.status}).encode())

def run_server():
    server = HTTPServer(('127.0.0.1', 8000), DashboardHandler)
    logger.info("Dashboard running at http://127.0.0.1:8000")
    server.serve_forever()

async def async_main():
    init_db()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    runner = JobRunner()
    try:
        await runner.start_loop()
    except KeyboardInterrupt:
        await runner.stop()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
