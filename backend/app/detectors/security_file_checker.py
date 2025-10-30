"""
Security File Checker

Checks for security.txt, robots.txt, and other security-related files
"""

import aiohttp
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SecurityFileChecker:
    """Checks for security-related files and their configurations"""
    
    SECURITY_FILES = {
        '/.well-known/security.txt': 'security_txt',
        '/security.txt': 'security_txt_root',
        '/robots.txt': 'robots_txt',
        '/.git/config': 'exposed_git',
        '/.env': 'exposed_env',
        '/.DS_Store': 'exposed_ds_store',
        '/backup.zip': 'exposed_backup',
        '/backup.sql': 'exposed_sql',
        '/config.php': 'exposed_config',
        '/wp-config.php': 'exposed_wp_config',
        '/.htaccess': 'exposed_htaccess',
    }
    
    @staticmethod
    async def check(url: str, timeout: int = 10) -> Dict:
        """
        Check for security-related files
        
        Args:
            url: Base URL to check
            timeout: Request timeout
            
        Returns:
            Dictionary with file findings
        """
        findings = {
            'has_issues': False,
            'files_found': [],
            'files_missing': [],
            'sensitive_exposed': [],
            'severity': 'low'
        }
        
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            base_url = url.rstrip('/')
            
            async with aiohttp.ClientSession() as session:
                for file_path, file_type in SecurityFileChecker.SECURITY_FILES.items():
                    full_url = f'{base_url}{file_path}'
                    
                    try:
                        async with session.get(
                            full_url,
                            timeout=aiohttp.ClientTimeout(total=timeout),
                            allow_redirects=False,
                            ssl=False
                        ) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                file_info = {
                                    'path': file_path,
                                    'type': file_type,
                                    'url': full_url,
                                    'size': len(content)
                                }
                                
                                # Check if it's a sensitive file exposure
                                if file_type in ['exposed_git', 'exposed_env', 'exposed_backup', 
                                                 'exposed_sql', 'exposed_config', 'exposed_wp_config',
                                                 'exposed_htaccess', 'exposed_ds_store']:
                                    file_info['severity'] = 'critical'
                                    file_info['description'] = f'Sensitive file exposed: {file_path}'
                                    file_info['remediation'] = 'Remove or restrict access to this file immediately'
                                    findings['sensitive_exposed'].append(file_info)
                                    findings['has_issues'] = True
                                    findings['severity'] = 'critical'
                                
                                # Check robots.txt for sensitive paths
                                elif file_type == 'robots_txt':
                                    sensitive_paths = SecurityFileChecker._analyze_robots_txt(content)
                                    if sensitive_paths:
                                        file_info['severity'] = 'medium'
                                        file_info['description'] = 'robots.txt reveals sensitive paths'
                                        file_info['sensitive_paths'] = sensitive_paths
                                        file_info['remediation'] = 'Review and remove sensitive path disclosures'
                                        findings['files_found'].append(file_info)
                                        findings['has_issues'] = True
                                        if findings['severity'] == 'low':
                                            findings['severity'] = 'medium'
                                    else:
                                        findings['files_found'].append(file_info)
                                
                                # Check security.txt
                                elif file_type in ['security_txt', 'security_txt_root']:
                                    file_info['severity'] = 'info'
                                    file_info['description'] = 'security.txt found (good practice)'
                                    findings['files_found'].append(file_info)
                                else:
                                    findings['files_found'].append(file_info)
                    
                    except aiohttp.ClientError:
                        # File not found or inaccessible
                        if file_type in ['security_txt', 'security_txt_root']:
                            findings['files_missing'].append({
                                'path': file_path,
                                'type': file_type,
                                'severity': 'info',
                                'description': 'security.txt not found (recommended for security disclosure)'
                            })
                    except Exception as e:
                        logger.debug(f"Error checking {full_url}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error checking security files for {url}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _analyze_robots_txt(content: str) -> list:
        """Analyze robots.txt for sensitive path disclosures"""
        sensitive_keywords = [
            'admin', 'login', 'password', 'secret', 'private',
            'backup', 'config', 'database', 'db', 'sql',
            'internal', 'dev', 'test', 'staging'
        ]
        
        sensitive_paths = []
        lines = content.lower().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('disallow:') or line.startswith('allow:'):
                path = line.split(':', 1)[1].strip()
                # Check if path contains sensitive keywords
                if any(keyword in path for keyword in sensitive_keywords):
                    sensitive_paths.append(path)
        
        return sensitive_paths

