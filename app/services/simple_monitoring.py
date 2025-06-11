"""
Simple monitoring service for Google Cloud
"""

import asyncio
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MonitoringService:
    """Simple monitoring service using standard logging"""
    
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
        self.metrics_store: Dict[str, List[Dict[str, Any]]] = {}
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Simple monitoring service started")
    
    async def stop_monitoring(self):
        """Stop monitoring tasks"""
        self.is_monitoring = False
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Simple monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect and analyze metrics every minute
                await self._collect_system_metrics()
                await self._check_alert_conditions()
                await self._cleanup_old_metrics()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _collect_system_metrics(self):
        """Collect basic system metrics"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Collect basic metrics
            metrics = [
                await self._get_memory_usage_metric(),
                await self._get_active_sessions_metric(),
            ]
            
            # Store metrics
            for metric in metrics:
                if metric:
                    metric_name = metric['name']
                    if metric_name not in self.metrics_store:
                        self.metrics_store[metric_name] = []
                    
                    self.metrics_store[metric_name].append({
                        'timestamp': current_time.isoformat(),
                        'value': metric['value'],
                        'metadata': metric.get('metadata', {})
                    })
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def _get_memory_usage_metric(self) -> Optional[Dict[str, Any]]:
        """Get memory usage metric"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            return {
                'name': 'memory_usage_percent',
                'value': memory_percent,
                'metadata': {}
            }
            
        except ImportError:
            # psutil not available, return error state
            return {
                'name': 'memory_usage_percent',
                'value': 0.0,
                'metadata': {'error': 'psutil not available', 'status': 'unavailable'}
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage metric: {e}")
            return None
    
    async def _get_active_sessions_metric(self) -> Optional[Dict[str, Any]]:
        """Get active sessions metric"""
        try:
            # Get actual session count from session manager if available
            from main import session_manager
            if session_manager:
                stats = await session_manager.get_session_stats()
                active_sessions = stats.get("total_active_sessions", 0)
            else:
                active_sessions = 0
            
            return {
                'name': 'active_sessions',
                'value': active_sessions,
                'metadata': {}
            }
            
        except Exception as e:
            logger.error(f"Failed to get active sessions metric: {e}")
            return None
    
    async def _check_alert_conditions(self):
        """Check if any alert conditions are met"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check memory usage
            await self._check_memory_alert(current_time)
            
        except Exception as e:
            logger.error(f"Failed to check alert conditions: {e}")
    
    async def _check_memory_alert(self, current_time: datetime):
        """Check memory usage alert condition"""
        try:
            if 'memory_usage_percent' in self.metrics_store:
                recent_metrics = [
                    m for m in self.metrics_store['memory_usage_percent']
                    if datetime.fromisoformat(m['timestamp']) > current_time - timedelta(minutes=5)
                ]
                
                if recent_metrics:
                    avg_memory = sum(m['value'] for m in recent_metrics) / len(recent_metrics)
                    
                    if avg_memory > 90:  # Alert if memory usage > 90%
                        await self._send_alert(
                            'high_memory_usage',
                            f"Memory usage is {avg_memory:.1f}% (threshold: 90%)",
                            'medium',
                            {'avg_memory': avg_memory, 'sample_size': len(recent_metrics)}
                        )
            
        except Exception as e:
            logger.error(f"Failed to check memory alert: {e}")
    
    async def _send_alert(self, alert_type: str, message: str, severity: str, metadata: Dict[str, Any]):
        """Send alert (log-based implementation)"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check if we've sent this alert recently (avoid spam)
            last_alert_time = self.last_alert_times.get(alert_type)
            if last_alert_time and current_time - last_alert_time < timedelta(minutes=15):
                return  # Don't send duplicate alerts within 15 minutes
            
            # Log alert
            logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}", extra={
                'alert_type': alert_type,
                'severity': severity,
                'metadata': metadata,
                'timestamp': current_time.isoformat()
            })
            
            # Update last alert time
            self.last_alert_times[alert_type] = current_time
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory buildup"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            for metric_name in self.metrics_store:
                self.metrics_store[metric_name] = [
                    m for m in self.metrics_store[metric_name]
                    if datetime.fromisoformat(m['timestamp']) > cutoff_time
                ]
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
    
    async def log_conversation_event(self, event_data: Dict[str, Any]):
        """Log conversation event for monitoring"""
        try:
            logger.info("Conversation event", extra=event_data)
        except Exception as e:
            logger.error(f"Failed to log conversation event: {e}")
    
    async def log_service_interaction(self, service_data: Dict[str, Any]):
        """Log service interaction for monitoring"""
        try:
            logger.info("Service interaction", extra=service_data)
        except Exception as e:
            logger.error(f"Failed to log service interaction: {e}")
    
    async def log_error_event(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """Log error event"""
        try:
            logger.error(f"Error event: {error_type} - {error_message}", extra={
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to log error event: {e}")
    
    async def log_message_status(self, message_id: str, status: str, timestamp: str):
        """Log WhatsApp message status for monitoring"""
        try:
            logger.info("Message status update", extra={
                'message_id': message_id,
                'status': status,
                'whatsapp_timestamp': timestamp,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to log message status: {e}")
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get recent metrics
            memory_health = "unknown"
            if 'memory_usage_percent' in self.metrics_store:
                recent_memory = [
                    m for m in self.metrics_store['memory_usage_percent']
                    if datetime.fromisoformat(m['timestamp']) > current_time - timedelta(minutes=5)
                ]
                if recent_memory:
                    avg_memory = sum(m['value'] for m in recent_memory) / len(recent_memory)
                    memory_health = "healthy" if avg_memory < 80 else "degraded"
            
            return {
                'timestamp': current_time.isoformat(),
                'overall_status': memory_health,
                'memory_health': memory_health,
                'metrics_collected': len(self.metrics_store),
                'monitoring_active': self.is_monitoring
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health summary: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': 'unknown',
                'error': str(e)
            }