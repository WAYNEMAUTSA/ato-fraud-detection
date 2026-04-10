"""
ATO Shield v2 - Simulator Routes
POST /simulate/start - Start transaction simulation
POST /simulate/stop - Stop transaction simulation
"""
from fastapi import APIRouter
from simulator.simulator import TransactionSimulator
import os
import threading

router = APIRouter()

# Global simulator instance
simulator_thread = None
simulator_instance = None


@router.post("/simulate/start")
async def start_simulation(
    count: int = 100,
    speed: float = 0.5,
    fraud_rate: float = 0.15
):
    """Start PaySim transaction simulation"""
    global simulator_thread, simulator_instance
    
    if simulator_thread and simulator_thread.is_alive():
        return {"status": "already_running", "message": "Simulation already in progress"}
    
    # Find PaySim data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "paysim dataset.csv")
    
    if not os.path.exists(data_path):
        return {"status": "error", "message": "PaySim dataset not found"}
    
    # Create simulator
    simulator_instance = TransactionSimulator(
        data_path=data_path,
        api_url="http://localhost:8000",
        api_key="ask_live_demo_key_12345"
    )
    
    # Run in background thread
    simulator_thread = threading.Thread(
        target=simulator_instance.run_simulation,
        kwargs={
            'count': count,
            'speed': speed,
            'fraud_weight': fraud_rate
        },
        daemon=True
    )
    simulator_thread.start()
    
    return {
        "status": "started",
        "message": f"Simulation started: {count} transactions at {speed}s intervals",
        "config": {
            "count": count,
            "speed": speed,
            "fraud_rate": fraud_rate
        }
    }


@router.post("/simulate/stop")
async def stop_simulation():
    """Stop running simulation"""
    global simulator_instance
    
    if simulator_instance:
        simulator_instance.stop()
        return {"status": "stopped", "message": "Simulation stopped"}
    else:
        return {"status": "not_running", "message": "No simulation in progress"}
