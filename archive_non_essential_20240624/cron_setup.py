"""
Cron Setup for Daily Trading System

Configures cron jobs to run the daily trading system 1 hour after market close.
"""

import os
import sys
import logging
from datetime import datetime, time
import pytz

logger = logging.getLogger(__name__)


class CronSetup:
    """
    Handles cron job setup for the daily trading system.
    """
    
    def __init__(self):
        self.script_path = os.path.abspath(__file__)
        self.daily_trading_script = os.path.join(
            os.path.dirname(self.script_path), 
            'daily_trading_system.py'
        )
        self.log_dir = os.path.join(os.path.dirname(self.script_path), 'logs')
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
    
    def generate_cron_entries(self) -> str:
        """
        Generate cron entries for the daily trading system.
        
        Returns:
            String with cron entries
        """
        cron_entries = []
        
        # Market close is typically 4:00 PM ET, so run at 5:00 PM ET (1 hour after)
        # Convert to UTC: ET is UTC-5 (EST) or UTC-4 (EDT)
        # For safety, use UTC-5 (EST) which means 10:00 PM UTC
        
        # Daily trading system - runs 1 hour after market close
        cron_entries.append({
            'schedule': '0 22 * * 1-5',  # 10:00 PM UTC, Mon-Fri
            'description': 'Daily Trading System - 1 hour after market close',
            'command': f'cd {os.path.dirname(self.daily_trading_script)} && python daily_trading_system.py >> logs/cron_daily_trading.log 2>&1'
        })
        
        # Weekend maintenance - runs Saturday morning
        cron_entries.append({
            'schedule': '0 6 * * 6',  # 6:00 AM UTC Saturday
            'description': 'Weekend maintenance and historical data population',
            'command': f'cd {os.path.dirname(self.daily_trading_script)} && python daily_trading_system.py --force >> logs/cron_weekend.log 2>&1'
        })
        
        # System health check - runs daily at 2:00 AM UTC
        cron_entries.append({
            'schedule': '0 2 * * *',  # 2:00 AM UTC daily
            'description': 'System health check and monitoring',
            'command': f'cd {os.path.dirname(self.daily_trading_script)} && python system_health_check.py >> logs/cron_health.log 2>&1'
        })
        
        return cron_entries
    
    def create_crontab_file(self, filename: str = 'crontab_entries.txt'):
        """
        Create a file with cron entries.
        
        Args:
            filename: Name of the file to create
        """
        cron_entries = self.generate_cron_entries()
        
        with open(filename, 'w') as f:
            f.write("# Daily Trading System Cron Entries\n")
            f.write("# Generated on: {}\n".format(datetime.now()))
            f.write("# Market close: 4:00 PM ET (9:00 PM UTC)\n")
            f.write("# Trading system runs: 5:00 PM ET (10:00 PM UTC)\n\n")
            
            for entry in cron_entries:
                f.write(f"# {entry['description']}\n")
                f.write(f"{entry['schedule']} {entry['command']}\n\n")
        
        logger.info(f"Cron entries written to {filename}")
        return filename
    
    def install_cron_jobs(self) -> bool:
        """
        Install cron jobs on the system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create cron entries file
            cron_file = self.create_crontab_file()
            
            # Read current crontab
            import subprocess
            
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], 
                                  capture_output=True, text=True)
            
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # Read new cron entries
            with open(cron_file, 'r') as f:
                new_entries = f.read()
            
            # Combine current and new entries
            combined_crontab = current_crontab + "\n" + new_entries
            
            # Write to temporary file
            temp_file = 'temp_crontab.txt'
            with open(temp_file, 'w') as f:
                f.write(combined_crontab)
            
            # Install new crontab
            result = subprocess.run(['crontab', temp_file], 
                                  capture_output=True, text=True)
            
            # Clean up
            os.remove(temp_file)
            os.remove(cron_file)
            
            if result.returncode == 0:
                logger.info("✅ Cron jobs installed successfully")
                return True
            else:
                logger.error(f"❌ Failed to install cron jobs: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error installing cron jobs: {e}")
            return False
    
    def show_cron_entries(self):
        """
        Display the cron entries that would be installed.
        """
        cron_entries = self.generate_cron_entries()
        
        print("📅 Daily Trading System Cron Entries")
        print("=" * 60)
        print(f"Script path: {self.daily_trading_script}")
        print(f"Log directory: {self.log_dir}")
        print()
        
        for i, entry in enumerate(cron_entries, 1):
            print(f"{i}. {entry['description']}")
            print(f"   Schedule: {entry['schedule']}")
            print(f"   Command: {entry['command']}")
            print()
        
        print("📝 To install these cron jobs:")
        print("   python cron_setup.py --install")
        print()
        print("📝 To view current cron jobs:")
        print("   crontab -l")
        print()
        print("📝 To remove all cron jobs:")
        print("   crontab -r")
    
    def create_systemd_service(self) -> str:
        """
        Create a systemd service file for the daily trading system.
        
        Returns:
            Path to the created service file
        """
        service_content = f"""[Unit]
Description=Daily Trading System
After=network.target

[Service]
Type=oneshot
User={os.getenv('USER', 'root')}
WorkingDirectory={os.path.dirname(self.daily_trading_script)}
ExecStart=/usr/bin/python3 {self.daily_trading_script}
StandardOutput=append:{self.log_dir}/systemd_daily_trading.log
StandardError=append:{self.log_dir}/systemd_daily_trading.log

[Install]
WantedBy=multi-user.target
"""
        
        service_file = '/etc/systemd/system/daily-trading-system.service'
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            logger.info(f"✅ Systemd service file created: {service_file}")
            return service_file
            
        except PermissionError:
            logger.warning("⚠️  Permission denied creating systemd service file")
            logger.info("Run with sudo or create manually:")
            logger.info(f"sudo tee {service_file} << EOF")
            logger.info(service_content)
            logger.info("EOF")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating systemd service: {e}")
            return None
    
    def create_timer_file(self) -> str:
        """
        Create a systemd timer file for the daily trading system.
        
        Returns:
            Path to the created timer file
        """
        timer_content = f"""[Unit]
Description=Daily Trading System Timer
Requires=daily-trading-system.service

[Timer]
# Run 1 hour after market close (5:00 PM ET = 10:00 PM UTC)
OnCalendar=Mon..Fri 22:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
        
        timer_file = '/etc/systemd/system/daily-trading-system.timer'
        
        try:
            with open(timer_file, 'w') as f:
                f.write(timer_content)
            
            logger.info(f"✅ Systemd timer file created: {timer_file}")
            return timer_file
            
        except PermissionError:
            logger.warning("⚠️  Permission denied creating systemd timer file")
            logger.info("Run with sudo or create manually:")
            logger.info(f"sudo tee {timer_file} << EOF")
            logger.info(timer_content)
            logger.info("EOF")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating systemd timer: {e}")
            return None
    
    def setup_systemd(self) -> bool:
        """
        Set up systemd service and timer for the daily trading system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create service file
            service_file = self.create_systemd_service()
            if not service_file:
                return False
            
            # Create timer file
            timer_file = self.create_timer_file()
            if not timer_file:
                return False
            
            # Reload systemd and enable timer
            import subprocess
            
            commands = [
                ['systemctl', 'daemon-reload'],
                ['systemctl', 'enable', 'daily-trading-system.timer'],
                ['systemctl', 'start', 'daily-trading-system.timer']
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"⚠️  Command failed: {' '.join(cmd)}")
                    logger.warning(f"   Error: {result.stderr}")
            
            logger.info("✅ Systemd timer setup completed")
            logger.info("📝 To check timer status: systemctl status daily-trading-system.timer")
            logger.info("📝 To view timer logs: journalctl -u daily-trading-system.service")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up systemd: {e}")
            return False


def main():
    """Main entry point for cron setup."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cron Setup for Daily Trading System')
    parser.add_argument('--show', action='store_true', help='Show cron entries')
    parser.add_argument('--install', action='store_true', help='Install cron jobs')
    parser.add_argument('--systemd', action='store_true', help='Set up systemd timer instead of cron')
    parser.add_argument('--create-file', action='store_true', help='Create cron entries file only')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    setup = CronSetup()
    
    if args.show:
        setup.show_cron_entries()
    
    elif args.create_file:
        filename = setup.create_crontab_file()
        print(f"✅ Cron entries file created: {filename}")
    
    elif args.install:
        success = setup.install_cron_jobs()
        if success:
            print("✅ Cron jobs installed successfully")
        else:
            print("❌ Failed to install cron jobs")
            sys.exit(1)
    
    elif args.systemd:
        success = setup.setup_systemd()
        if success:
            print("✅ Systemd timer setup completed")
        else:
            print("❌ Failed to set up systemd timer")
            sys.exit(1)
    
    else:
        # Default: show cron entries
        setup.show_cron_entries()


if __name__ == "__main__":
    main() 