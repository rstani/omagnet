from datetime import datetime

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from netmiko import ConnectHandler
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@db:5432/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()


# Database model
class JobResult(Base):
    __tablename__ = "job_results"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    ip = Column(String)
    os = Column(String)
    command = Column(String)
    username = Column(String)
    result = Column(Text)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


class CommandRequest(BaseModel):
    ip: str
    os: str
    command: str
    username: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def execute_command_and_parse(db, job_id: str, command_request: CommandRequest):
    device = {
        "device_type": command_request.os,
        "host": command_request.ip,
        "username": command_request.username,
        "password": command_request.password,
    }

    try:
        # Connect to the device and execute the command
        # connection = ConnectHandler(**device)
        # raw_output = connection.send_command(command_request.command, use_textfsm=True)
        # connection.disconnect()
        # Simulate command execution
        raw_output = f"Test output for {job_id}"

        # Update the job result in the database
        db_job = db.query(JobResult).filter(JobResult.job_id == job_id).first()
        db_job.status = "completed"
        db_job.result = str(raw_output)
        db.commit()

    except Exception as e:
        # Update the job result in case of error
        db_job = db.query(JobResult).filter(JobResult.job_id == job_id).first()
        db_job.status = "error"
        db_job.result = str(e)
        db.commit()


@app.post("/execute-command/")
async def execute_command(
    command_request: CommandRequest,
    background_tasks: BackgroundTasks,
    db: SessionLocal = Depends(get_db),
):
    # Generate job_id based on the current number of records in the database
    job_count = db.query(func.count(JobResult.id)).scalar()
    job_id = str(job_count + 1)

    db_job = JobResult(
        job_id=job_id,
        ip=command_request.ip,
        os=command_request.os,
        command=command_request.command,
        username=command_request.username,
        status="Processing",
    )
    db.add(db_job)
    db.commit()

    background_tasks.add_task(execute_command_and_parse, db, job_id, command_request)
    return {"job_id": job_id}


@app.get("/result/{job_id}")
async def get_result(job_id: str, db: SessionLocal = Depends(get_db)):
    db_job = db.query(JobResult).filter(JobResult.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    if db_job.status == "Processing":
        return {"status": "still processing"}
    return {"status": db_job.status, "result": db_job.result}
