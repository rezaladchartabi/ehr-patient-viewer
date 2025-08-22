#!/usr/bin/env python3
"""
Infrastructure Diagnostic Script
Identifies current infrastructure issues and technical debt
"""

import os
import sys
import subprocess
import socket
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any

class InfrastructureDiagnostic:
    def __init__(self):
        self.results = {}
        self.issues = []
        
    def check_port_usage(self, port: int) -> Dict[str, Any]:
        """Check if a port is in use and by what process"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use, find the process
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == port:
                                return {
                                    "in_use": True,
                                    "process": {
                                        "pid": proc.info['pid'],
                                        "name": proc.info['name'],
                                        "cmdline": proc.info['cmdline']
                                    }
                                }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return {"in_use": True, "process": None}
            else:
                return {"in_use": False, "process": None}
        except Exception as e:
            return {"in_use": False, "error": str(e)}
    
    def check_process_management(self) -> Dict[str, Any]:
        """Check current process management issues"""
        issues = []
        
        # Check for uvicorn processes
        uvicorn_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'uvicorn' in proc.info['name'] or any('uvicorn' in str(cmd) for cmd in proc.info['cmdline'] or []):
                    uvicorn_processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cmdline": proc.info['cmdline']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if len(uvicorn_processes) > 1:
            issues.append(f"Multiple uvicorn processes running: {len(uvicorn_processes)}")
        
        # Check for zombie processes
        zombie_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                if proc.info['status'] == 'zombie':
                    zombie_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if zombie_count > 0:
            issues.append(f"Zombie processes found: {zombie_count}")
        
        return {
            "uvicorn_processes": uvicorn_processes,
            "zombie_processes": zombie_count,
            "issues": issues
        }
    
    def check_environment_setup(self) -> Dict[str, Any]:
        """Check environment setup issues"""
        issues = []
        env_info = {}
        
        # Check working directory
        cwd = os.getcwd()
        env_info["current_working_directory"] = cwd
        
        # Check if we're in the right directory for backend
        if not os.path.exists("main.py"):
            issues.append("main.py not found in current directory")
        
        # Check Python environment
        env_info["python_version"] = sys.version
        env_info["python_executable"] = sys.executable
        
        # Check environment variables
        relevant_env_vars = [
            "FHIR_BASE_URL", "RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW",
            "REACT_APP_API_BASE_URL", "PYTHONPATH"
        ]
        
        env_info["environment_variables"] = {}
        for var in relevant_env_vars:
            value = os.getenv(var)
            if value:
                env_info["environment_variables"][var] = value
            else:
                issues.append(f"Environment variable {var} not set")
        
        # Check file permissions
        try:
            if os.path.exists("main.py"):
                env_info["main_py_readable"] = os.access("main.py", os.R_OK)
                env_info["main_py_executable"] = os.access("main.py", os.X_OK)
        except Exception as e:
            issues.append(f"File permission check failed: {e}")
        
        return {
            "environment_info": env_info,
            "issues": issues
        }
    
    def check_service_connectivity(self) -> Dict[str, Any]:
        """Check service connectivity issues"""
        services = {
            "backend_8006": ("localhost", 8006),
            "frontend_3000": ("localhost", 3000),
            "fhir_8080": ("localhost", 8080)
        }
        
        connectivity_results = {}
        issues = []
        
        for service_name, (host, port) in services.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                connectivity_results[service_name] = {
                    "reachable": result == 0,
                    "host": host,
                    "port": port
                }
                
                if result != 0:
                    issues.append(f"Service {service_name} not reachable")
                    
            except Exception as e:
                connectivity_results[service_name] = {
                    "reachable": False,
                    "error": str(e),
                    "host": host,
                    "port": port
                }
                issues.append(f"Service {service_name} connection error: {e}")
        
        return {
            "connectivity": connectivity_results,
            "issues": issues
        }
    
    def check_docker_availability(self) -> Dict[str, Any]:
        """Check if Docker is available and working"""
        docker_info = {}
        issues = []
        
        try:
            # Check if Docker is installed
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                docker_info["installed"] = True
                docker_info["version"] = result.stdout.strip()
            else:
                docker_info["installed"] = False
                issues.append("Docker not installed or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_info["installed"] = False
            issues.append("Docker not found in PATH")
        
        # Check if Docker daemon is running
        if docker_info.get("installed"):
            try:
                result = subprocess.run(["docker", "info"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    docker_info["daemon_running"] = True
                else:
                    docker_info["daemon_running"] = False
                    issues.append("Docker daemon not running")
            except subprocess.TimeoutExpired:
                docker_info["daemon_running"] = False
                issues.append("Docker daemon not responding")
        
        return {
            "docker_info": docker_info,
            "issues": issues
        }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent_used": (disk.used / disk.total) * 100
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run complete infrastructure diagnostic"""
        print("🔍 Running infrastructure diagnostic...")
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "port_usage": {
                "8005": self.check_port_usage(8005),
                "8006": self.check_port_usage(8006),
                "3000": self.check_port_usage(3000),
                "8080": self.check_port_usage(8080)
            },
            "process_management": self.check_process_management(),
            "environment_setup": self.check_environment_setup(),
            "service_connectivity": self.check_service_connectivity(),
            "docker_availability": self.check_docker_availability(),
            "system_resources": self.check_system_resources()
        }
        
        # Collect all issues
        all_issues = []
        for section, data in self.results.items():
            if isinstance(data, dict) and "issues" in data:
                all_issues.extend(data["issues"])
        
        self.results["summary"] = {
            "total_issues": len(all_issues),
            "critical_issues": [issue for issue in all_issues if "critical" in issue.lower()],
            "all_issues": all_issues
        }
        
        return self.results
    
    def print_report(self):
        """Print diagnostic report"""
        print("\n" + "="*80)
        print("INFRASTRUCTURE DIAGNOSTIC REPORT")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Summary
        summary = self.results.get("summary", {})
        print(f"\n📊 SUMMARY:")
        print(f"   Total Issues Found: {summary.get('total_issues', 0)}")
        print(f"   Critical Issues: {len(summary.get('critical_issues', []))}")
        
        # Port Usage
        print(f"\n🔌 PORT USAGE:")
        for port, info in self.results.get("port_usage", {}).items():
            if info.get("in_use"):
                process = info.get("process")
                if process:
                    print(f"   Port {port}: IN USE by {process.get('name', 'Unknown')} (PID: {process.get('pid', 'Unknown')})")
                else:
                    print(f"   Port {port}: IN USE by unknown process")
            else:
                print(f"   Port {port}: AVAILABLE")
        
        # Process Management
        pm_info = self.results.get("process_management", {})
        print(f"\n🔄 PROCESS MANAGEMENT:")
        print(f"   Uvicorn Processes: {len(pm_info.get('uvicorn_processes', []))}")
        print(f"   Zombie Processes: {pm_info.get('zombie_processes', 0)}")
        if pm_info.get("issues"):
            for issue in pm_info["issues"]:
                print(f"   ⚠️  {issue}")
        
        # Environment Setup
        env_info = self.results.get("environment_setup", {})
        print(f"\n🏗️  ENVIRONMENT SETUP:")
        print(f"   Working Directory: {env_info.get('environment_info', {}).get('current_working_directory', 'Unknown')}")
        print(f"   Python Version: {env_info.get('environment_info', {}).get('python_version', 'Unknown')}")
        if env_info.get("issues"):
            for issue in env_info["issues"]:
                print(f"   ⚠️  {issue}")
        
        # Service Connectivity
        connectivity = self.results.get("service_connectivity", {})
        print(f"\n🌐 SERVICE CONNECTIVITY:")
        for service, info in connectivity.get("connectivity", {}).items():
            status = "✅ REACHABLE" if info.get("reachable") else "❌ NOT REACHABLE"
            print(f"   {service}: {status}")
        if connectivity.get("issues"):
            for issue in connectivity["issues"]:
                print(f"   ⚠️  {issue}")
        
        # Docker Availability
        docker_info = self.results.get("docker_availability", {})
        print(f"\n🐳 DOCKER AVAILABILITY:")
        docker_installed = docker_info.get("docker_info", {}).get("installed", False)
        docker_running = docker_info.get("docker_info", {}).get("daemon_running", False)
        print(f"   Docker Installed: {'✅ Yes' if docker_installed else '❌ No'}")
        print(f"   Docker Daemon Running: {'✅ Yes' if docker_running else '❌ No'}")
        if docker_info.get("issues"):
            for issue in docker_info["issues"]:
                print(f"   ⚠️  {issue}")
        
        # System Resources
        resources = self.results.get("system_resources", {})
        if "error" not in resources:
            print(f"\n💻 SYSTEM RESOURCES:")
            print(f"   CPU Usage: {resources.get('cpu_usage_percent', 0):.1f}%")
            memory = resources.get("memory", {})
            print(f"   Memory Usage: {memory.get('percent_used', 0):.1f}% ({memory.get('available_gb', 0):.1f}GB available)")
            disk = resources.get("disk", {})
            print(f"   Disk Usage: {disk.get('percent_used', 0):.1f}% ({disk.get('free_gb', 0):.1f}GB free)")
        
        # All Issues
        if summary.get("all_issues"):
            print(f"\n🚨 ALL ISSUES FOUND:")
            for i, issue in enumerate(summary["all_issues"], 1):
                print(f"   {i}. {issue}")
        
        print("\n" + "="*80)

def main():
    """Run infrastructure diagnostic"""
    diagnostic = InfrastructureDiagnostic()
    results = diagnostic.run_full_diagnostic()
    diagnostic.print_report()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"infrastructure_diagnostic_{timestamp}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on issues
    total_issues = results.get("summary", {}).get("total_issues", 0)
    if total_issues > 0:
        print(f"\n⚠️  {total_issues} infrastructure issues found!")
        return 1
    else:
        print(f"\n✅ No infrastructure issues found!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
