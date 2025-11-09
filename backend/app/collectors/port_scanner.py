"""
Port Scanner Module

Uses nmap and masscan for comprehensive port scanning.
Falls back to Python socket scanning if tools are not available.
"""

import asyncio
import logging
import socket
import subprocess
import shutil
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class PortScanner:
    """
    Advanced port scanner using nmap/masscan with Python fallback.
    """
    
    # Common ports to scan
    COMMON_PORTS = [
        21,    # FTP
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        53,    # DNS
        80,    # HTTP
        110,   # POP3
        143,   # IMAP
        443,   # HTTPS
        445,   # SMB
        3306,  # MySQL
        3389,  # RDP
        5432,  # PostgreSQL
        5900,  # VNC
        6379,  # Redis
        8080,  # HTTP Alt
        8443,  # HTTPS Alt
        27017, # MongoDB
    ]
    
    # Top 100 ports (nmap default)
    TOP_100_PORTS = [
        7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106, 110, 111,
        113, 119, 135, 139, 143, 144, 179, 199, 389, 427, 443, 444, 445, 465,
        513, 514, 515, 543, 544, 548, 554, 587, 631, 646, 873, 990, 993, 995,
        1025, 1026, 1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755, 1900, 2000,
        2001, 2049, 2121, 2717, 3000, 3128, 3306, 3389, 3986, 4899, 5000, 5009,
        5051, 5060, 5101, 5190, 5357, 5432, 5631, 5666, 5800, 5900, 6000, 6001,
        6646, 7070, 8000, 8008, 8009, 8080, 8081, 8443, 8888, 9100, 9999, 10000,
        32768, 49152, 49153, 49154, 49155, 49156, 49157
    ]
    
    @staticmethod
    def check_tool_availability() -> Dict[str, bool]:
        """Check if nmap and masscan are installed"""
        return {
            'nmap': shutil.which('nmap') is not None,
            'masscan': shutil.which('masscan') is not None,
        }
    
    @staticmethod
    async def scan_ports(
        target: str,
        ports: Optional[List[int]] = None,
        scan_type: str = "common",
        timeout: int = 300
    ) -> Dict:
        """
        Scan ports on target using best available method.
        
        Args:
            target: IP address or hostname
            ports: List of specific ports to scan (None = use scan_type)
            scan_type: "common" (18 ports), "top100" (100 ports), or "full" (1-1000)
            timeout: Scan timeout in seconds
            
        Returns:
            Dictionary with scan results
        """
        result = {
            'target': target,
            'open_ports': [],
            'services': {},
            'scan_method': None,
            'scan_duration': 0,
            'error': None
        }
        
        # Determine ports to scan
        if ports is None:
            if scan_type == "common":
                ports = PortScanner.COMMON_PORTS
            elif scan_type == "top100":
                ports = PortScanner.TOP_100_PORTS
            elif scan_type == "full":
                ports = list(range(1, 1001))  # Scan 1-1000
            else:
                ports = PortScanner.COMMON_PORTS
        
        # Check available tools
        tools = PortScanner.check_tool_availability()
        
        # Try methods in order of preference: masscan > nmap > python
        if tools['masscan'] and len(ports) > 50:
            # Use masscan for large port ranges (faster)
            logger.info(f"Using masscan to scan {len(ports)} ports on {target}")
            result = await PortScanner._scan_with_masscan(target, ports, timeout)
            result['scan_method'] = 'masscan'
        elif tools['nmap']:
            # Use nmap for detailed scanning
            logger.info(f"Using nmap to scan {len(ports)} ports on {target}")
            result = await PortScanner._scan_with_nmap(target, ports, timeout)
            result['scan_method'] = 'nmap'
        else:
            # Fallback to Python socket scanning
            logger.info(f"Using Python socket to scan {len(ports)} ports on {target}")
            result = await PortScanner._scan_with_python(target, ports, timeout)
            result['scan_method'] = 'python_socket'
        
        return result
    
    @staticmethod
    async def _scan_with_nmap(target: str, ports: List[int], timeout: int) -> Dict:
        """Scan using nmap"""
        result = {
            'target': target,
            'open_ports': [],
            'services': {},
            'scan_method': 'nmap',
            'scan_duration': 0,
            'error': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Convert ports list to nmap format
            port_string = ','.join(map(str, ports))
            
            # Run nmap with XML output for easier parsing
            cmd = [
                'nmap',
                '-p', port_string,
                '-sV',  # Service version detection
                '--open',  # Only show open ports
                '-T4',  # Aggressive timing
                '--host-timeout', f'{timeout}s',
                '-oX', '-',  # XML output to stdout
                target
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            result['scan_duration'] = time.time() - start_time
            
            if process.returncode == 0:
                # Parse XML output
                xml_output = stdout.decode('utf-8')
                root = ET.fromstring(xml_output)
                
                # Extract open ports and services
                for port in root.findall('.//port'):
                    state = port.find('state')
                    if state is not None and state.get('state') == 'open':
                        port_id = int(port.get('portid'))
                        result['open_ports'].append(port_id)
                        
                        # Extract service info
                        service = port.find('service')
                        if service is not None:
                            result['services'][port_id] = {
                                'name': service.get('name', 'unknown'),
                                'product': service.get('product', ''),
                                'version': service.get('version', ''),
                            }
                
                logger.info(f"Nmap found {len(result['open_ports'])} open ports on {target}")
            else:
                error_msg = stderr.decode('utf-8')
                logger.error(f"Nmap scan failed: {error_msg}")
                result['error'] = error_msg
                
        except asyncio.TimeoutError:
            logger.warning(f"Nmap scan timeout for {target}")
            result['error'] = 'Scan timeout'
        except Exception as e:
            logger.error(f"Nmap scan error: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    async def _scan_with_masscan(target: str, ports: List[int], timeout: int) -> Dict:
        """Scan using masscan (very fast for large port ranges)"""
        result = {
            'target': target,
            'open_ports': [],
            'services': {},
            'scan_method': 'masscan',
            'scan_duration': 0,
            'error': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Convert ports list to masscan format
            port_string = ','.join(map(str, ports))
            
            # Run masscan
            cmd = [
                'masscan',
                target,
                '-p', port_string,
                '--rate', '1000',  # Packets per second
                '--wait', '0',  # Don't wait for responses
                '--open',  # Only show open ports
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            result['scan_duration'] = time.time() - start_time
            
            if process.returncode == 0:
                # Parse masscan output
                output = stdout.decode('utf-8')
                
                for line in output.split('\n'):
                    if 'open' in line.lower():
                        # Parse line like: "Discovered open port 443/tcp on 192.168.1.1"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.isdigit() or '/' in part:
                                port_num = int(part.split('/')[0])
                                if port_num not in result['open_ports']:
                                    result['open_ports'].append(port_num)
                
                result['open_ports'].sort()
                logger.info(f"Masscan found {len(result['open_ports'])} open ports on {target}")
            else:
                error_msg = stderr.decode('utf-8')
                logger.error(f"Masscan scan failed: {error_msg}")
                result['error'] = error_msg
                
        except asyncio.TimeoutError:
            logger.warning(f"Masscan scan timeout for {target}")
            result['error'] = 'Scan timeout'
        except Exception as e:
            logger.error(f"Masscan scan error: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    async def _scan_with_python(target: str, ports: List[int], timeout: int) -> Dict:
        """Fallback: Scan using Python sockets (slower but always available)"""
        result = {
            'target': target,
            'open_ports': [],
            'services': {},
            'scan_method': 'python_socket',
            'scan_duration': 0,
            'error': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Resolve hostname to IP
            try:
                ip = socket.gethostbyname(target)
            except socket.gaierror:
                result['error'] = f"Could not resolve hostname: {target}"
                return result
            
            # Scan ports concurrently (but limit concurrency to avoid overwhelming)
            semaphore = asyncio.Semaphore(50)  # Max 50 concurrent connections
            
            async def check_port(port: int):
                async with semaphore:
                    try:
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(ip, port),
                            timeout=2.0
                        )
                        writer.close()
                        await writer.wait_closed()
                        return port
                    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                        return None
            
            # Scan all ports
            tasks = [check_port(port) for port in ports]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect open ports
            for port in results:
                if port is not None and isinstance(port, int):
                    result['open_ports'].append(port)
            
            result['open_ports'].sort()
            result['scan_duration'] = time.time() - start_time
            
            logger.info(f"Python socket scan found {len(result['open_ports'])} open ports on {target}")
            
        except Exception as e:
            logger.error(f"Python socket scan error: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    @staticmethod
    def get_service_name(port: int) -> str:
        """Get common service name for a port"""
        common_services = {
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            445: 'SMB',
            3306: 'MySQL',
            3389: 'RDP',
            5432: 'PostgreSQL',
            5900: 'VNC',
            6379: 'Redis',
            8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt',
            27017: 'MongoDB',
        }
        return common_services.get(port, f'Port-{port}')
