import time
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import tracemalloc
from openai import APIConnectionError

from utils.logger import get_logger
from models.UserProfile import UserProfile
from core.personal_finance_health_analyzer import personal_finance_health_analyzer

app = FastAPI()

class AnalysisRequest(BaseModel):
    mode: Literal['basic', 'advanced']
    data: UserProfile

@app.post('/personal-finance-health-analyzer')
async def personal_finance_health_analysis(req: AnalysisRequest):
    logger = get_logger()
    logger.info('---------- New Request Received ----------')
    try:
        if req.mode == 'basic' or req.mode == 'advanced':
            logger.info('Request is valid.')
            tracemalloc.start()
            start_time = time.perf_counter()

            report_data = await personal_finance_health_analyzer(req.data, req.mode)

            end_time = time.perf_counter()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            logger.info(f"Total Test Runtime: {end_time - start_time : 0.3f} s.")
            logger.info(f"Peak memory usage: {peak / 10**6:.3f} MB")
            logger.info('------------------------------------------')
            return report_data
        else:
            logger.error('Invalid report generation mode received.')
            raise HTTPException(status_code=400, detail="Invalid mode specified.")
    except APIConnectionError:
        raise HTTPException(status_code=503, detail="Could not reach our servers. Please check your connection and try again.")
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Analysis failed due to an unexpected error. Please try later.")

if __name__ == '__main__':
    with open('data/test_data/average_profile.json') as file:
        user_data = json.load(file)
    
    output = asyncio.run(
        personal_finance_health_analysis(
            AnalysisRequest(
                mode='advanced',
                data=UserProfile(**user_data)
            )
        )
    )

    with open('sample_output.json', 'w') as file:
        json.dump(output.model_dump(), file, indent=2)

    ### fix 999 issue
    