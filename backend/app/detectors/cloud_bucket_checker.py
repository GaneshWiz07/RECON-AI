"""
Cloud Bucket Checker

Detects publicly accessible cloud storage buckets (S3, Azure Blob, GCS)
"""

import aiohttp
import logging
from typing import Dict, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CloudBucketChecker:
    """Checks for publicly accessible cloud storage buckets"""
    
    # Cloud storage URL patterns
    S3_PATTERNS = [
        'https://{bucket}.s3.amazonaws.com',
        'https://{bucket}.s3-{region}.amazonaws.com',
        'https://s3.amazonaws.com/{bucket}',
        'https://s3-{region}.amazonaws.com/{bucket}',
    ]
    
    AZURE_PATTERNS = [
        'https://{account}.blob.core.windows.net/{container}',
    ]
    
    GCS_PATTERNS = [
        'https://storage.googleapis.com/{bucket}',
        'https://{bucket}.storage.googleapis.com',
    ]
    
    FIREBASE_PATTERNS = [
        'https://{app}.firebaseio.com',
        'https://storage.googleapis.com/{app}.appspot.com',
    ]
    
    @staticmethod
    async def check(domain: str, timeout: int = 10) -> Dict:
        """
        Check for publicly accessible cloud buckets
        
        Args:
            domain: Target domain to check
            timeout: Request timeout
            
        Returns:
            Dictionary with bucket findings
        """
        findings = {
            'has_issues': False,
            'buckets': [],
            'severity': 'low'
        }
        
        try:
            # Extract potential bucket names from domain
            bucket_names = CloudBucketChecker._extract_bucket_names(domain)
            
            # Check S3 buckets
            for bucket_name in bucket_names:
                s3_finding = await CloudBucketChecker._check_s3_bucket(bucket_name, timeout)
                if s3_finding:
                    findings['buckets'].append(s3_finding)
                    findings['has_issues'] = True
                    findings['severity'] = s3_finding['severity']
                
                # Check GCS
                gcs_finding = await CloudBucketChecker._check_gcs_bucket(bucket_name, timeout)
                if gcs_finding:
                    findings['buckets'].append(gcs_finding)
                    findings['has_issues'] = True
                    if findings['severity'] == 'low':
                        findings['severity'] = gcs_finding['severity']
                
                # Check Azure
                azure_finding = await CloudBucketChecker._check_azure_blob(bucket_name, timeout)
                if azure_finding:
                    findings['buckets'].append(azure_finding)
                    findings['has_issues'] = True
                    if findings['severity'] == 'low':
                        findings['severity'] = azure_finding['severity']
                
                # Check Firebase
                firebase_finding = await CloudBucketChecker._check_firebase(bucket_name, timeout)
                if firebase_finding:
                    findings['buckets'].append(firebase_finding)
                    findings['has_issues'] = True
                    if findings['severity'] == 'low':
                        findings['severity'] = firebase_finding['severity']
                        
        except Exception as e:
            logger.error(f"Error checking cloud buckets for {domain}: {str(e)}")
            findings['error'] = str(e)
        
        return findings
    
    @staticmethod
    def _extract_bucket_names(domain: str) -> List[str]:
        """Extract potential bucket names from domain"""
        # Clean domain
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.split('/')[0].split(':')[0]
        
        # Generate variations
        bucket_names = [
            domain,
            domain.replace('.', '-'),
            domain.split('.')[0],  # First part only
            f'{domain.split(".")[0]}-assets',
            f'{domain.split(".")[0]}-backup',
            f'{domain.split(".")[0]}-data',
        ]
        
        return list(set(bucket_names))
    
    @staticmethod
    async def _check_s3_bucket(bucket_name: str, timeout: int) -> Dict:
        """Check if S3 bucket is publicly accessible"""
        url = f'https://{bucket_name}.s3.amazonaws.com'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False
                ) as response:
                    content = await response.text()
                    
                    # Check if bucket exists and is accessible
                    if response.status == 200:
                        # Bucket is publicly listable
                        return {
                            'type': 'aws_s3',
                            'url': url,
                            'bucket': bucket_name,
                            'severity': 'critical',
                            'access': 'public_read',
                            'description': f'S3 bucket "{bucket_name}" is publicly accessible and listable',
                            'remediation': 'Restrict bucket permissions and enable bucket policies'
                        }
                    elif response.status == 403 and 'AccessDenied' not in content:
                        # Bucket exists but listing is denied (still a finding)
                        return {
                            'type': 'aws_s3',
                            'url': url,
                            'bucket': bucket_name,
                            'severity': 'high',
                            'access': 'exists_no_list',
                            'description': f'S3 bucket "{bucket_name}" exists (listing denied)',
                            'remediation': 'Verify bucket permissions and naming'
                        }
        except aiohttp.ClientError:
            pass
        except Exception as e:
            logger.debug(f"Error checking S3 bucket {bucket_name}: {str(e)}")
        
        return None
    
    @staticmethod
    async def _check_gcs_bucket(bucket_name: str, timeout: int) -> Dict:
        """Check if Google Cloud Storage bucket is publicly accessible"""
        url = f'https://storage.googleapis.com/{bucket_name}'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return {
                            'type': 'gcs',
                            'url': url,
                            'bucket': bucket_name,
                            'severity': 'critical',
                            'access': 'public_read',
                            'description': f'GCS bucket "{bucket_name}" is publicly accessible',
                            'remediation': 'Update IAM permissions to restrict public access'
                        }
        except:
            pass
        
        return None
    
    @staticmethod
    async def _check_azure_blob(account_name: str, timeout: int) -> Dict:
        """Check if Azure Blob storage is publicly accessible"""
        # Try common container names
        containers = ['assets', 'files', 'images', 'backup', 'data', 'public']
        
        for container in containers:
            url = f'https://{account_name}.blob.core.windows.net/{container}'
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        allow_redirects=False,
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            return {
                                'type': 'azure_blob',
                                'url': url,
                                'account': account_name,
                                'container': container,
                                'severity': 'critical',
                                'access': 'public_read',
                                'description': f'Azure Blob container "{container}" is publicly accessible',
                                'remediation': 'Change container access level to private'
                            }
            except:
                continue
        
        return None
    
    @staticmethod
    async def _check_firebase(app_name: str, timeout: int) -> Dict:
        """Check if Firebase database is publicly accessible"""
        url = f'https://{app_name}.firebaseio.com/.json'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and data != {'error': 'Permission denied'}:
                            return {
                                'type': 'firebase',
                                'url': url,
                                'app': app_name,
                                'severity': 'critical',
                                'access': 'public_read',
                                'description': f'Firebase database "{app_name}" has public read access',
                                'remediation': 'Update Firebase security rules to restrict access'
                            }
        except:
            pass
        
        return None

