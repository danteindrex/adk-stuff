"""
Enhanced Monitoring Service for Production Scale
Includes metrics collection, alerting, and performance monitoring
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json

# Google Cloud Monitoring
from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

# OpenTelemetry
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Structured metric data"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: str  # counter, gauge, histogram

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric_name: str
    threshold: float
    comparison: str  # gt, lt, eq
    duration_minutes: int
    severity: str  # critical, warning, info

class EnhancedMonitoringService:
    """Production-ready monitoring service with comprehensive metrics and alerting"""
    
    def __init__(self):
        self.metrics_buffer: List[MetricData] = []
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, datetime] = {}
        self.performance_history = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        
        # Initialize monitoring clients
        self._init_google_cloud_monitoring()
        self._init_prometheus_metrics()
        self._init_opentelemetry()
        self._setup_alert_rules()
        
        # Background tasks
        self._monitoring_task = None
        self._metrics_flush_task = None
        self._alert_check_task = None
        
    def _init_google_cloud_monitoring(self):
        """Initialize Google Cloud Monitoring client"""
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.logging_client = cloud_logging.Client()
            self.project_name = f"projects/{settings.GOOGLE_CLOUD_PROJECT}"
            logger.info("Google Cloud Monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Monitoring: {e}")
            self.monitoring_client = None
            self.logging_client = None
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        self.registry = CollectorRegistry()
        
        # Core metrics
        self.request_counter = Counter(
            'whatsapp_requests_total',
            'Total WhatsApp requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'whatsapp_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_sessions = Gauge(
            'active_sessions_total',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.agent_operations = Counter(
            'agent_operations_total',
            'Total agent operations',
            ['agent_name', 'operation', 'status'],
            registry=self.registry
        )
        
        self.system_memory = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_cpu = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        logger.info("Prometheus metrics initialized")
    
    def _init_opentelemetry(self):
        """Initialize OpenTelemetry tracing and metrics"""
        try:
            # Set up tracing
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
            
            # Set up metrics
            metrics.set_meter_provider(MeterProvider())
            self.meter = metrics.get_meter(__name__)
            
            logger.info("OpenTelemetry initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
    
    def _setup_alert_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="error_rate",
                threshold=0.05,  # 5% error rate
                comparison="gt",
                duration_minutes=5,
                severity="critical"
            ),
            AlertRule(
                name="high_response_time",
                metric_name="avg_response_time",
                threshold=5.0,  # 5 seconds
                comparison="gt",
                duration_minutes=3,
                severity="warning"
            ),
            AlertRule(
                name="low_success_rate",
                metric_name="success_rate",
                threshold=0.95,  # 95% success rate
                comparison="lt",
                duration_minutes=5,
                severity="critical"
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="memory_usage_percent",
                threshold=85.0,  # 85% memory usage
                comparison="gt",
                duration_minutes=10,
                severity="warning"
            )
        ]
    
    async def start_monitoring(self):
        """Start all monitoring background tasks"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._metrics_flush_task = asyncio.create_task(self._metrics_flush_loop())
        self._alert_check_task = asyncio.create_task(self._alert_check_loop())
        logger.info("Enhanced monitoring started")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        tasks = [self._monitoring_task, self._metrics_flush_task, self._alert_check_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("Enhanced monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop - collect system metrics"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_flush_loop(self):
        """Flush metrics to external systems"""
        while True:
            try:
                await self._flush_metrics_to_gcp()
                await asyncio.sleep(60)  # Flush every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics flush loop: {e}")
                await asyncio.sleep(120)
    
    async def _alert_check_loop(self):
        """Check alert conditions"""
        while True:
            try:
                await self._check_alerts()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(120)
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update Prometheus metrics
            self.system_cpu.set(cpu_percent)
            self.system_memory.set(memory.used)
            
            # Store in buffer for GCP
            timestamp = datetime.now()
            metrics = [
                MetricData("cpu_usage_percent", cpu_percent, timestamp, {}, "gauge"),
                MetricData("memory_usage_percent", memory.percent, timestamp, {}, "gauge"),
                MetricData("memory_used_bytes", memory.used, timestamp, {}, "gauge"),
                MetricData("disk_usage_percent", disk.percent, timestamp, {}, "gauge"),
            ]
            
            self.metrics_buffer.extend(metrics)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def _flush_metrics_to_gcp(self):
        """Flush metrics to Google Cloud Monitoring"""
        if not self.monitoring_client or not self.metrics_buffer:
            return
        
        try:
            series = []
            for metric in self.metrics_buffer:
                series.append({
                    'metric': {
                        'type': f'custom.googleapis.com/uganda_egov/{metric.name}',
                        'labels': metric.labels
                    },
                    'resource': {
                        'type': 'global',
                        'labels': {'project_id': settings.GOOGLE_CLOUD_PROJECT}
                    },
                    'points': [{
                        'interval': {
                            'end_time': {'seconds': int(metric.timestamp.timestamp())}
                        },
                        'value': {'double_value': metric.value}
                    }]
                })
            
            if series:
                self.monitoring_client.create_time_series(
                    name=self.project_name,
                    time_series=series
                )
                logger.debug(f"Flushed {len(series)} metrics to GCP")
            
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics to GCP: {e}")
    
    async def _check_alerts(self):
        """Check alert conditions and trigger alerts"""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            try:
                metric_value = await self._get_metric_value(rule.metric_name)
                if metric_value is None:
                    continue
                
                # Check threshold
                triggered = False
                if rule.comparison == "gt" and metric_value > rule.threshold:
                    triggered = True
                elif rule.comparison == "lt" and metric_value < rule.threshold:
                    triggered = True
                elif rule.comparison == "eq" and metric_value == rule.threshold:
                    triggered = True
                
                if triggered:
                    # Check if alert should fire (duration check)
                    if rule.name not in self.active_alerts:
                        self.active_alerts[rule.name] = current_time
                    elif current_time - self.active_alerts[rule.name] >= timedelta(minutes=rule.duration_minutes):
                        await self._fire_alert(rule, metric_value)
                else:
                    # Clear alert if condition no longer met
                    if rule.name in self.active_alerts:
                        del self.active_alerts[rule.name]
                        await self._clear_alert(rule)
                        
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}: {e}")
    
    async def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value for a metric"""
        try:
            if metric_name == "error_rate":
                total_requests = sum(self.request_counts.values())
                error_requests = sum(count for status, count in self.request_counts.items() if status.startswith('5'))
                return error_requests / total_requests if total_requests > 0 else 0.0
            
            elif metric_name == "avg_response_time":
                all_times = []
                for times in self.response_times.values():
                    all_times.extend(times)
                return sum(all_times) / len(all_times) if all_times else 0.0
            
            elif metric_name == "success_rate":
                total_requests = sum(self.request_counts.values())
                success_requests = sum(count for status, count in self.request_counts.items() if status.startswith('2'))
                return success_requests / total_requests if total_requests > 0 else 1.0
            
            elif metric_name == "memory_usage_percent":
                return psutil.virtual_memory().percent
            
            return None
        except Exception as e:
            logger.error(f"Error getting metric value for {metric_name}: {e}")
            return None
    
    async def _fire_alert(self, rule: AlertRule, value: float):
        """Fire an alert"""
        alert_message = f"ALERT: {rule.name} - {rule.metric_name} is {value} (threshold: {rule.threshold})"
        
        # Log to Google Cloud Logging
        if self.logging_client:
            self.logging_client.logger("uganda-egov-alerts").log_struct({
                "severity": rule.severity.upper(),
                "message": alert_message,
                "rule": asdict(rule),
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
        
        logger.warning(alert_message)
    
    async def _clear_alert(self, rule: AlertRule):
        """Clear an alert"""
        clear_message = f"CLEARED: {rule.name} - condition no longer met"
        
        if self.logging_client:
            self.logging_client.logger("uganda-egov-alerts").log_struct({
                "severity": "INFO",
                "message": clear_message,
                "rule": asdict(rule),
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(clear_message)
    
    # Public API methods
    async def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record a request for monitoring"""
        # Update Prometheus metrics
        self.request_counter.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
        # Update internal counters
        self.request_counts[str(status_code)] += 1
        self.response_times[endpoint].append(duration)
        
        # Keep only recent response times
        if len(self.response_times[endpoint]) > 100:
            self.response_times[endpoint] = self.response_times[endpoint][-100:]
    
    async def record_agent_operation(self, agent_name: str, operation: str, status: str, duration: float = None):
        """Record an agent operation"""
        self.agent_operations.labels(agent_name=agent_name, operation=operation, status=status).inc()
        
        if duration:
            self.metrics_buffer.append(MetricData(
                f"agent_{agent_name}_{operation}_duration",
                duration,
                datetime.now(),
                {"agent": agent_name, "operation": operation},
                "histogram"
            ))
    
    async def update_active_sessions(self, count: int):
        """Update active sessions count"""
        self.active_sessions.set(count)
    
    async def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log an error with context"""
        self.error_counts[error_type] += 1
        
        error_data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "count": self.error_counts[error_type]
        }
        
        if self.logging_client:
            self.logging_client.logger("uganda-egov-errors").log_struct(error_data)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            total_requests = sum(self.request_counts.values())
            error_requests = sum(count for status, count in self.request_counts.items() if status.startswith('5'))
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_total_gb": memory.total / (1024**3)
                },
                "requests": {
                    "total": total_requests,
                    "error_rate": error_requests / total_requests if total_requests > 0 else 0,
                    "status_codes": dict(self.request_counts)
                },
                "errors": dict(self.error_counts),
                "active_alerts": list(self.active_alerts.keys()),
                "metrics_buffer_size": len(self.metrics_buffer)
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest(self.registry).decode('utf-8')