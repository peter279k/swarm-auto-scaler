import time
import docker
import logging
import requests


LOG_FILE_PATH = '/app/scaler.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROMETHEUS_URL = 'http://prometheus:9090'
DOCKER_CLIENT = docker.from_env()
CHECK_INTERVAL = 30  # seconds between scaling checks

# Scaling rules: define thresholds for each service
prefix = 'fmsa_'
services = [
    'api_gateway', 'data_analysis_service', 'ioht_data_collector',
    'fhir_generator', 'fhir_converter', 'fhir_ig_manager',
    'fhir_profile_manager', 'fhir_data_manager', 'terminology_manager',
    'fhir-server-adapter',
]

rule_template = {}
for service in services:
    service_name = f'{prefix}{service}'
    rule_template[f'{prefix}{service}'] = {
        'metric_query': 'avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_service_name="' + service_name + '"}[2m])) * 100',
        'scale_up_threshold': 50,
        'scale_down_threshold': 30,
        'min_replicas': 3,
        'max_replicas': 12,
        'scale_up_step': 1,
        'scale_down_step': 1,
        'cooldown': 120,
    }

SCALING_RULES = dict(rule_template)

# Track last scaling time to enforce cooldowns
last_scaled = {}


def query_prometheus(query):
    '''Execute a PromQL query and return the numeric result.'''
    try:
        response = requests.get(
            f'{PROMETHEUS_URL}/api/v1/query',
            params={'query': query},
            timeout=10
        )
        data = response.json()
        if data['status'] == 'success' and data['data']['result']:
            return float(data['data']['result'][0]['value'][1])
    except Exception as e:
        logger.error(f'Prometheus query failed: {e}')
    return None


def get_current_replicas(service_name):
    '''Get the current replica count for a Swarm service.'''
    try:
        service = DOCKER_CLIENT.services.get(service_name)
        return service.attrs['Spec']['Mode']['Replicated']['Replicas']
    except Exception as e:
        logger.error(f'Failed to get replicas for {service_name}: {e}')
        return None


def scale_service(service_name, target_replicas):
    '''Scale a Swarm service to the target replica count.'''
    try:
        service = DOCKER_CLIENT.services.get(service_name)
        service.scale(target_replicas)
        logger.info(f'Scaled {service_name} to {target_replicas} replicas')
        last_scaled[service_name] = time.time()
    except Exception as e:
        logger.error(f'Failed to scale {service_name}: {e}')


def check_and_scale():
    '''Evaluate metrics and scale services as needed.'''
    for service_name, rules in SCALING_RULES.items():
        # Check cooldown period
        if service_name in last_scaled:
            elapsed = time.time() - last_scaled[service_name]
            if elapsed < rules['cooldown']:
                logger.debug(f"{service_name}: In cooldown ({elapsed:.0f}s / {rules['cooldown']}s)")
                continue

        # Query the metric
        metric_value = query_prometheus(rules['metric_query'])
        if metric_value is None:
            continue

        current_replicas = get_current_replicas(service_name)
        if current_replicas is None:
            continue

        logger.info(f'{service_name}: CPU={metric_value:.1f}%, replicas={current_replicas}')

        # Scale up
        if metric_value > rules['scale_up_threshold']:
            target = min(current_replicas + rules['scale_up_step'], rules['max_replicas'])
            if target > current_replicas:
                logger.info(f'{service_name}: Scaling UP {current_replicas} -> {target}')
                scale_service(service_name, target)

        # Scale down
        elif metric_value < rules['scale_down_threshold']:
            target = max(current_replicas - rules['scale_down_step'], rules['min_replicas'])
            if target < current_replicas:
                logger.info(f'{service_name}: Scaling DOWN {current_replicas} -> {target}')
                scale_service(service_name, target)


if __name__ == '__main__':
    logger.info('Swarm auto-scaler starting')
    while True:
        check_and_scale()
        time.sleep(CHECK_INTERVAL)
