import asyncio
import logging
from src.database.db import get_connection
from src.jobs.queue import JobQueue
from src.models.domain import JobStatus, GenerationState
from src.browser.manager import BrowserManager
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager, AuthState

logger = logging.getLogger(__name__)

class JobRunner:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.running = False
        
    async def start_loop(self):
        self.running = True
        logger.info("Starting JobRunner loop...")
        
        while self.running:
            conn = get_connection()
            queue = JobQueue(conn)
            
            job = queue.get_next_job()
            if job:
                logger.info(f"Picked up job {job.id}")
                queue.update_job_status(job.id, JobStatus.RUNNING)
                
                gen_id = queue.add_generation(job.id, GenerationState.QUEUED.value)
                
                try:
                    await self._process_job(job, queue, gen_id)
                except Exception as e:
                    logger.error(f"Job {job.id} failed with exception: {e}")
                    queue.update_job_status(job.id, JobStatus.FAILED, error_message=str(e))
                finally:
                    conn.close()
            else:
                conn.close()
                await asyncio.sleep(5)
                
    async def _process_job(self, job, queue, gen_id: int):
        def update_gen_state(state: GenerationState):
            queue.update_generation_state(gen_id, state.value)
            
        update_gen_state(GenerationState.OPENING_BROWSER)
        page = await self.browser_manager.get_page()
        adapter = GoogleFlowAdapter(page)
        
        update_gen_state(GenerationState.OPENING_FLOW)
        await adapter.open_flow()
        
        update_gen_state(GenerationState.CHECKING_AUTH)
        auth_status = await AuthManager.check_auth_status(page)
        
        if auth_status != AuthState.AUTHENTICATED:
            logger.warning("Not authenticated or auth unknown. Waiting for manual auth.")
            update_gen_state(GenerationState.AUTH_REQUIRED)
            
            auth_success = await AuthManager.wait_for_manual_auth(page)
            if not auth_success:
                raise Exception("Manual authentication timed out or failed.")
                
        update_gen_state(GenerationState.PREPARING_PROMPT)
        
        # We pass the job directly since it has the attributes
        update_gen_state(GenerationState.SUBMITTING)
        success = await adapter.submit_prompt(job)
        
        if not success:
            raise Exception("Failed to submit prompt to Flow UI.")
            
        update_gen_state(GenerationState.GENERATING)
        gen_success = await adapter.wait_for_generation()
        
        if not gen_success:
            raise Exception("Generation timed out or failed in Flow UI.")
            
        update_gen_state(GenerationState.COMPLETED)
        
        update_gen_state(GenerationState.DOWNLOADING)
        output_path = await adapter.download_asset(job.id)
        
        if not output_path:
            raise Exception("Failed to download the generated asset.")
            
        update_gen_state(GenerationState.SUCCESS)
        queue.update_job_status(job.id, JobStatus.SUCCESS, output_path=output_path)
        logger.info(f"Job {job.id} completed successfully. Asset at {output_path}")

    async def stop(self):
        self.running = False
        await self.browser_manager.stop()
