from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime
import time  # Simulate a long-running process

app = FastAPI()

# Simulated storage for job results
job_results = {}

class CommandRequest(BaseModel):
    ip: str
    command: str
    username: str
    password: str

def execute_command_and_parse(job_id: str, command_request: CommandRequest):
    time.sleep(5)  # Simulate time taken to run the command
    # Here you would execute the command on the network device
    raw_output = f"Simulated raw output from {command_request.command}"

    # Simulate template-based parsing
    parsed_output = {"Ouput": raw_output, "timestamp": datetime.now().isoformat()}

    # If no template is found, use AI (simulated)
    if "no template" in parsed_output:
        parsed_output = f"AI Parsed: {raw_output}"
    # Store the result
    job_results[job_id] = parsed_output

@app.post("/execute-command/")
async def execute_command(command_request: CommandRequest, background_tasks: BackgroundTasks):
    job_id = str(len(job_results) + 1)
    job_results[job_id] = "Processing"
    background_tasks.add_task(execute_command_and_parse, job_id, command_request)
    return {"job_id": job_id}

@app.get("/result/{job_id}")
async def get_result(job_id: str):
    result = job_results.get(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Job ID not found")
    if result == "Processing":
        return {"status": "still processing"}
    return {"status": "completed", "result": result}
