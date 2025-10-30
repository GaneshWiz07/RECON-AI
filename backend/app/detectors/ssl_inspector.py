"""
SSL/TLS Inspector

Checks SSL certificates for expiration, weak ciphers, and misconfigurations
"""

import ssl
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SSLInspector:
    """Inspects SSL/TLS certificates for security issues"""
    
    WEAK_PROTOCOLS = ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']
    WEAK_CIPHERS = ['DES', 'RC4', 'MD5', 'NULL', 'EXPORT', 'anon']
    
    @staticmethod
    async def inspect(hostname: str, port: int = 443, timeout: int = 10) -> Dict:
        """
        Inspect SSL/TLS certificate and configuration
        
        Args:
            hostname: Target hostname
            port: Target port (default 443)
            timeout: Connection timeout
            
        Returns:
            Dictionary with SSL findings
        """
        findings = {
            'has_issues': False,
            'issues': [],
            'certificate': {},
            'severity': 'low',
            'valid': True
        }
        
        try:
            # Clean hostname
            if hostname.startswith(('http://', 'https://')):
                hostname = urlparse(hostname).netloc
            hostname = hostname.split(':')[0]  # Remove port if present
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    protocol = ssock.version()
                    
                    # Parse certificate info
                    if cert:
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (not_after - datetime.now()).days
                        
                        findings['certificate'] = {
                            'subject': dict(x[0] for x in cert.get('subject', [])),
                            'issuer': dict(x[0] for x in cert.get('issuer', [])),
                            'valid_from': not_before.isoformat(),
                            'valid_until': not_after.isoformat(),
                            'days_until_expiry': days_until_expiry,
                            'san': SSLInspector._extract_san(cert)
                        }
                        
                        # Check expiration
                        if days_until_expiry < 0:
                            findings['issues'].append({
                                'type': 'expired_certificate',
                                'severity': 'critical',
                                'description': f'Certificate expired {abs(days_until_expiry)} days ago'
                            })
                            findings['has_issues'] = True
                            findings['severity'] = 'critical'
                            findings['valid'] = False
                        elif days_until_expiry < 30:
                            findings['issues'].append({
                                'type': 'expiring_soon',
                                'severity': 'high',
                                'description': f'Certificate expires in {days_until_expiry} days'
                            })
                            findings['has_issues'] = True
                            if findings['severity'] == 'low':
                                findings['severity'] = 'high'
                        
                        # Check if self-signed
                        subject = findings['certificate']['subject']
                        issuer = findings['certificate']['issuer']
                        if subject == issuer:
                            findings['issues'].append({
                                'type': 'self_signed',
                                'severity': 'high',
                                'description': 'Certificate is self-signed'
                            })
                            findings['has_issues'] = True
                            if findings['severity'] == 'low':
                                findings['severity'] = 'high'
                    
                    # Check protocol version
                    if protocol in SSLInspector.WEAK_PROTOCOLS:
                        findings['issues'].append({
                            'type': 'weak_protocol',
                            'severity': 'critical',
                            'description': f'Using weak protocol: {protocol}'
                        })
                        findings['has_issues'] = True
                        findings['severity'] = 'critical'
                    
                    # Check cipher suite
                    if cipher:
                        cipher_name = cipher[0]
                        findings['certificate']['cipher'] = cipher_name
                        findings['certificate']['protocol'] = protocol
                        
                        if any(weak in cipher_name.upper() for weak in SSLInspector.WEAK_CIPHERS):
                            findings['issues'].append({
                                'type': 'weak_cipher',
                                'severity': 'high',
                                'description': f'Using weak cipher suite: {cipher_name}'
                            })
                            findings['has_issues'] = True
                            if findings['severity'] == 'low':
                                findings['severity'] = 'high'
                    
        except ssl.SSLError as e:
            logger.warning(f"SSL error for {hostname}:{port} - {str(e)}")
            findings['issues'].append({
                'type': 'ssl_error',
                'severity': 'high',
                'description': f'SSL/TLS error: {str(e)}'
            })
            findings['has_issues'] = True
            findings['severity'] = 'high'
            findings['valid'] = False
        except socket.timeout:
            logger.warning(f"Timeout connecting to {hostname}:{port}")
            findings['error'] = 'Connection timeout'
        except Exception as e:
            logger.error(f"Error inspecting SSL for {hostname}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _extract_san(cert: Dict) -> list:
        """Extract Subject Alternative Names from certificate"""
        san_list = []
        if 'subjectAltName' in cert:
            for san_type, san_value in cert['subjectAltName']:
                if san_type == 'DNS':
                    san_list.append(san_value)
        return san_list

