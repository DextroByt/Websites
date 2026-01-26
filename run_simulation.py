import subprocess
import time
import sys
import os

def run_simulation():
    print("🚀 Starting RioMart Simulation...")

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    warehouse_dir = os.path.join(base_dir, "RioMart_Warehouse")
    agent_dir = os.path.join(base_dir, "Supply_Agent")

    # Start Warehouse
    print(f"📦 Launching Warehouse (Port 9001)...")
    # Using Popen to run in background
    # shell=False ensures we can terminate it properly, but on Windows shell=True is often needed for new consoles.
    # We will use simple Popen.
    warehouse_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=warehouse_dir,
        shell=True
    )
    
    # Wait a moment for Warehouse to boot
    time.sleep(2)

    # Start Supply Agent
    print(f"🤖 Launching Supply Agent (Port 9002)...")
    agent_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=agent_dir,
        shell=True
    )

    print("\n✅ System LIVE! Both services are running.")
    print("-------------------------------------------------")
    print("📊 Warehouse Dashboard : http://localhost:9001")
    print("🎛️  Agent Console      : http://localhost:9002")
    print("-------------------------------------------------")
    print("Logs will appear in this terminal (mixed) or in the separate windows depending on your OS.")
    print("PRESS CTRL+C TO STOP ALL SERVICES.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if warehouse_process.poll() is not None:
                print("❌ Warehouse process died unexpectedly.")
                break
            if agent_process.poll() is not None:
                print("❌ Agent process died unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation...")
        
        # Windows requires specific kill commands often if shell=True
        # but basic terminate usually works for the handle.
        # For robustness on Windows specifically:
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(warehouse_process.pid)])
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(agent_process.pid)])
        
        print("Done.")

if __name__ == "__main__":
    run_simulation()
