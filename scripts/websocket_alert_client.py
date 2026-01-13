"""
WebSocket Alert Client Example
==============================

Example client that connects to Autonomous Multi-Agent Business Intelligence System's WebSocket alert endpoint
and displays real-time anomaly alerts.

Usage:
    python scripts/websocket_alert_client.py

Requirements:
    pip install websockets
"""

import asyncio
import websockets
import json
from datetime import datetime
import sys


class AlertClient:
    """WebSocket client for receiving real-time anomaly alerts"""
    
    def __init__(self, uri="ws://localhost:8000/ws/alerts"):
        self.uri = uri
        self.websocket = None
        self.running = False
    
    async def connect(self):
        """Establish WebSocket connection"""
        print(f"🔗 Connecting to {self.uri}...")
        
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            print("✅ Connected successfully!")
            
            # Wait for connection acknowledgment
            message = await self.websocket.recv()
            data = json.loads(message)
            
            if data.get('type') == 'connection':
                print(f"📊 Monitoring Status:")
                monitoring = data.get('monitoring', {})
                print(f"   - Metrics tracked: {monitoring.get('metrics', 0)}")
                print(f"   - Check interval: {monitoring.get('check_interval_minutes', 0)} minutes")
                print("\n⏳ Waiting for anomaly alerts...")
                print("   (Press Ctrl+C to exit)\n")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.running = False
    
    async def listen(self):
        """Listen for incoming alerts"""
        if not self.websocket:
            print("❌ Not connected")
            return
        
        try:
            while self.running:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=30.0
                    )
                    
                    # Parse alert
                    alert = json.loads(message)
                    
                    # Display alert
                    self.display_alert(alert)
                    
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.websocket.send("ping")
                    print("💓 Heartbeat sent...")
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Connection closed by server")
            self.running = False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.running = False
    
    def display_alert(self, alert):
        """Display formatted alert"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Get severity emoji
        severity = alert.get('severity', 'info')
        emoji = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵'
        }.get(severity, '⚪')
        
        # Format deviation with color indicator
        deviation = alert.get('deviation_percent', 0)
        direction = '📈' if deviation > 0 else '📉'
        
        print(f"\n{emoji} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🚨 ANOMALY DETECTED [{timestamp}]")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"Metric:     {alert.get('metric_name', 'Unknown')}")
        print(f"Severity:   {severity.upper()}")
        print(f"Deviation:  {direction} {deviation:+.1f}%")
        print(f"Current:    {alert.get('current_value', 0):.2f}")
        print(f"Baseline:   {alert.get('baseline_value', 0):.2f} (7-day avg)")
        
        if alert.get('root_cause_analysis'):
            print(f"\n💡 Analysis:")
            print(f"   {alert['root_cause_analysis']}")
        
        print(f"{'━' * 56}\n")
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("\n👋 Disconnected")
    
    async def run(self):
        """Main run loop"""
        await self.connect()
        
        if self.running:
            await self.listen()
        
        await self.disconnect()


async def main():
    """Main entry point"""
    print("\n╔════════════════════════════════════════════════════╗")
    print("║   Autonomous Multi-Agent Business Intelligence System - Real-time Alert Client          ║")
    print("╚════════════════════════════════════════════════════╝\n")
    
    # Check if custom URI provided
    uri = "ws://localhost:8000/ws/alerts"
    if len(sys.argv) > 1:
        uri = sys.argv[1]
    
    # Create and run client
    client = AlertClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted by user")
        await client.disconnect()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
