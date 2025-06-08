"""
Monitoring and analytics service for Google Cloud
"""

import asyncio
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.core.logging_config import StructuredLogger

# Google Cloud imports
from google.cloud import logging as cloud_logging
from google.cloud import monitoring_v3

logger = StructuredLogger(__name__)

class MonitoringService:
    """Service for monitoring system performance and health using Google Cloud"""
    
    def __init__(self):
        self.monitoring_task: Optional[asyncio.Task] = None
        self.performance_buffer: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            'error_rate_5min': 0.10,  # 10% error rate in 5 minutes
            'response_time_avg': 10000,  # 10 seconds average response time
            'failed_authentications': 20,  # 20 failed logins in 10 minutes
            'service_downtime': 300,  # 5 minutes of service unavailability
        }
        self.last_alert_times: Dict[str, datetime] = {}
        self.is_monitoring = False
        
        # Initialize Google Cloud clients
        self._initialize_cloud_logging()
        self._initialize_cloud_monitoring()
    
    def _initialize_cloud_logging(self):
        """Initialize Google Cloud Logging client"""
        try:
            self.logging_client = cloud_logging.Client()
            self.logging_client.setup_logging()
            logger.info("Google Cloud Logging initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Logging: {e}")
            self.logging_client = None
    
    def _initialize_cloud_monitoring(self):
        """Initialize Google Cloud Monitoring client"""
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.project_name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', 'default-project')}"
            logger.info("Google Cloud Monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Monitoring: {e}")
            self.monitoring_client = None
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop monitoring tasks"""
        self.is_monitoring = False
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining performance metrics
        await self._flush_performance_buffer()
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect and analyze metrics every minute
                await self._collect_system_metrics()
                await self._check_alert_conditions()
                await self._flush_performance_buffer()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=e)
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Collect various metrics
            metrics = [
                await self._get_response_time_metric(),
                await self._get_error_rate_metric(),
                await self._get_active_sessions_metric(),
                await self._get_service_health_metrics(),
                await self._get_memory_usage_metric()
            ]
            
            # Add to performance buffer
            for metric in metrics:
                if metric:
                    self.performance_buffer.append({
                        'timestamp': current_time.isoformat(),
                        'metric_name': metric['name'],
                        'metric_value': metric['value'],
                        'metadata': metric.get('metadata', {})
                    })
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=e)
    
    async def _get_response_time_metric(self) -> Optional[Dict[str, Any]]:
        """Get average response time metric"""
        try:
            # Get response times from last 5 minutes
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            result = self.supabase.client.table('conversation_logs').select('processing_time_ms').gte('timestamp', cutoff_time.isoformat()).execute()
            
            if result.data:
                response_times = [log.get('processing_time_ms', 0) for log in result.data if log.get('processing_time_ms')]
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    return {
                        'name': 'avg_response_time_5min',
                        'value': avg_response_time,
                        'metadata': {'sample_size': len(response_times)}
                    }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get response time metric", error=e)
            return None
    
    async def _get_error_rate_metric(self) -> Optional[Dict[str, Any]]:
        """Get error rate metric"""
        try:
            # Get error rate from last 5 minutes
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            result = self.supabase.client.table('conversation_logs').select('success').gte('timestamp', cutoff_time.isoformat()).execute()
            
            if result.data:
                total_requests = len(result.data)
                failed_requests = len([log for log in result.data if not log.get('success', True)])
                error_rate = failed_requests / total_requests if total_requests > 0 else 0
                
                return {
                    'name': 'error_rate_5min',
                    'value': error_rate,
                    'metadata': {
                        'total_requests': total_requests,
                        'failed_requests': failed_requests
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get error rate metric", error=e)
            return None
    
    async def _get_active_sessions_metric(self) -> Optional[Dict[str, Any]]:
        """Get active sessions metric"""
        try:
            active_sessions = await self.supabase.get_active_sessions_count()
            
            return {
                'name': 'active_sessions',
                'value': active_sessions,
                'metadata': {}
            }
            
        except Exception as e:
            logger.error("Failed to get active sessions metric", error=e)
            return None
    
    async def _get_service_health_metrics(self) -> Optional[Dict[str, Any]]:
        """Get service health metrics"""
        try:
            service_health = await self.supabase.get_service_health_status()
            
            # Calculate overall health score
            healthy_services = sum(1 for service in service_health.values() if service.get('status') == 'healthy')
            total_services = len(service_health)
            health_score = healthy_services / total_services if total_services > 0 else 1.0
            
            return {
                'name': 'service_health_score',
                'value': health_score,
                'metadata': {
                    'healthy_services': healthy_services,
                    'total_services': total_services,
                    'service_details': service_health
                }
            }
            
        except Exception as e:
            logger.error("Failed to get service health metrics", error=e)
            return None
    
    async def _get_memory_usage_metric(self) -> Optional[Dict[str, Any]]:
        """Get memory usage metric (simplified)"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            return {
                'name': 'memory_usage_percent',
                'value': memory_percent,
                'metadata': {}
            }
            
        except ImportError:
            # psutil not available, return mock data
            return {
                'name': 'memory_usage_percent',
                'value': 45.0,  # Mock value
                'metadata': {'mock': True}
            }
        except Exception as e:
            logger.error("Failed to get memory usage metric", error=e)
            return None
    
    async def _check_alert_conditions(self):
        """Check if any alert conditions are met"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check error rate
            await self._check_error_rate_alert(current_time)
            
            # Check response time
            await self._check_response_time_alert(current_time)
            
            # Check service health
            await self._check_service_health_alert(current_time)
            
        except Exception as e:
            logger.error("Failed to check alert conditions", error=e)
    
    async def _check_error_rate_alert(self, current_time: datetime):
        """Check error rate alert condition"""
        try:
            cutoff_time = current_time - timedelta(minutes=5)
            
            result = self.supabase.client.table('conversation_logs').select('success').gte('timestamp', cutoff_time.isoformat()).execute()
            
            if result.data and len(result.data) >= 10:  # Only alert if we have enough data
                total_requests = len(result.data)
                failed_requests = len([log for log in result.data if not log.get('success', True)])
                error_rate = failed_requests / total_requests
                
                if error_rate > self.alert_thresholds['error_rate_5min']:
                    await self._send_alert(
                        'high_error_rate',
                        f"Error rate is {error_rate:.2%} (threshold: {self.alert_thresholds['error_rate_5min']:.2%})",
                        'high',
                        {'error_rate': error_rate, 'total_requests': total_requests, 'failed_requests': failed_requests}
                    )
            
        except Exception as e:
            logger.error("Failed to check error rate alert", error=e)
    
    async def _check_response_time_alert(self, current_time: datetime):
        """Check response time alert condition"""
        try:
            cutoff_time = current_time - timedelta(minutes=5)
            
            result = self.supabase.client.table('conversation_logs').select('processing_time_ms').gte('timestamp', cutoff_time.isoformat()).execute()
            
            if result.data:
                response_times = [log.get('processing_time_ms', 0) for log in result.data if log.get('processing_time_ms')]
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    
                    if avg_response_time > self.alert_thresholds['response_time_avg']:
                        await self._send_alert(
                            'high_response_time',
                            f"Average response time is {avg_response_time:.0f}ms (threshold: {self.alert_thresholds['response_time_avg']}ms)",
                            'medium',
                            {'avg_response_time': avg_response_time, 'sample_size': len(response_times)}
                        )
            
        except Exception as e:
            logger.error("Failed to check response time alert", error=e)
    
    async def _check_service_health_alert(self, current_time: datetime):
        """Check service health alert condition"""
        try:
            service_health = await self.supabase.get_service_health_status()
            
            for service_name, health_data in service_health.items():
                if health_data.get('status') == 'degraded' or health_data.get('success_rate', 1.0) < 0.8:
                    await self._send_alert(
                        'service_degraded',
                        f"Service {service_name} is degraded (success rate: {health_data.get('success_rate', 0):.2%})",
                        'high',
                        {'service': service_name, 'health_data': health_data}
                    )
            
        except Exception as e:
            logger.error("Failed to check service health alert", error=e)
    
    async def _send_alert(self, alert_type: str, message: str, severity: str, metadata: Dict[str, Any]):
        """Send alert to admin team"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check if we've sent this alert recently (avoid spam)
            last_alert_time = self.last_alert_times.get(alert_type)
            if last_alert_time and current_time - last_alert_time < timedelta(minutes=15):
                return  # Don't send duplicate alerts within 15 minutes
            
            # Store alert in database
            alert_data = {
                'timestamp': current_time.isoformat(),
                'alert_type': alert_type,
                'message': message,
                'severity': severity,
                'acknowledged': False,
                'metadata': metadata
            }
            
            self.supabase.client.table('admin_alerts').insert(alert_data).execute()
            
            # Update last alert time
            self.last_alert_times[alert_type] = current_time
            
            # Log alert
            logger.warning("Alert sent", alert_type=alert_type, severity=severity, message=message)
            
            # In production, you would also send to WhatsApp admin group, email, etc.
            # await self._send_whatsapp_alert(message)
            
        except Exception as e:
            logger.error("Failed to send alert", error=e, alert_type=alert_type)
    
    async def _flush_performance_buffer(self):
        """Flush performance metrics buffer to database"""
        if self.performance_buffer:
            try:
                # Insert all buffered metrics
                self.supabase.client.table('system_performance').insert(self.performance_buffer).execute()
                
                logger.debug("Performance metrics flushed", count=len(self.performance_buffer))
                self.performance_buffer.clear()
                
            except Exception as e:
                logger.error("Failed to flush performance buffer", error=e)
                # Keep buffer for next attempt, but limit size
                if len(self.performance_buffer) > 1000:
                    self.performance_buffer = self.performance_buffer[-500:]  # Keep last 500
    
    async def log_conversation_event(self, event_data: Dict[str, Any]):
        """Log conversation event for monitoring"""
        try:
            await self.supabase.log_conversation_event(event_data)
        except Exception as e:
            logger.error("Failed to log conversation event", error=e)
    
    async def log_service_interaction(self, service_data: Dict[str, Any]):
        """Log service interaction for monitoring"""
        try:
            await self.supabase.log_service_interaction(service_data)
        except Exception as e:
            logger.error("Failed to log service interaction", error=e)
    
    async def log_error_event(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """Log error event"""
        try:
            error_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'severity': 'error',
                'resolved': False
            }
            
            self.supabase.client.table('error_logs').insert(error_data).execute()
            
        except Exception as e:
            logger.error("Failed to log error event", error=e)
    
    async def log_message_status(self, message_id: str, status: str, timestamp: str):
        """Log WhatsApp message status for monitoring"""
        try:
            # Add to performance buffer for batch processing
            self.performance_buffer.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metric_name': 'message_status',
                'metric_value': 1,
                'metadata': {
                    'message_id': message_id,
                    'status': status,
                    'whatsapp_timestamp': timestamp
                }
            })
            
        except Exception as e:
            logger.error("Failed to log message status", error=e)
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get recent metrics
            cutoff_time = current_time - timedelta(minutes=5)
            
            # Active sessions
            active_sessions = await self.supabase.get_active_sessions_count()
            
            # Error rate
            error_summary = await self.supabase.get_recent_error_summary(1)  # Last hour
            total_errors = sum(error['count'] for error in error_summary)
            
            # Service health
            service_health = await self.supabase.get_service_health_status()
            healthy_services = sum(1 for service in service_health.values() if service.get('status') == 'healthy')
            total_services = len(service_health)
            
            return {
                'timestamp': current_time.isoformat(),
                'overall_status': 'healthy' if healthy_services == total_services and total_errors < 10 else 'degraded',
                'active_sessions': active_sessions,
                'total_errors_1h': total_errors,
                'service_health_score': healthy_services / total_services if total_services > 0 else 1.0,
                'services': service_health
            }
            
        except Exception as e:
            logger.error("Failed to get system health summary", error=e)
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'unknown',
                'error': str(e)
            }