import time

import docker
import logging
import threading
import sys
lgr = logging.getLogger(__name__)

# client = docker.from_env()
# docker==7.0.0

class StatMonitor(threading.Thread):
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.ram_usage = None
        self.cpu_usage = None
        self.monitor = True

    def get_cpu_usage_percent(self, cpu_stats, precpu_stats):
        """
        Fow windows check https://github.com/docker/cli/blob/9714adc6c797755f63053726c56bc1c17c0c9204/cli/command/container/stats_helpers.go#L185C6-L185C32
        :param cpu_stats:
        :param precpu_stats:
        :return:
        """
        cpu_percent = 0.0
        previous_cpu = float(precpu_stats["cpu_usage"]["total_usage"])
        if 'system_cpu_usage' in precpu_stats:
            previous_system = float(precpu_stats["system_cpu_usage"])
        else:
            previous_system = 0.0

        cpu_delta = float(cpu_stats["cpu_usage"]["total_usage"]) - previous_cpu
        system_delta = float(cpu_stats["system_cpu_usage"]) - previous_system
        online_cpus = float(cpu_stats["online_cpus"])

        if online_cpus == 0.0:
            online_cpus = float(len(cpu_stats["cpu_usage"]["percpu_usage"]))

        if system_delta > 0.0 and cpu_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0

        return cpu_percent

    def run(self):
        max_mem_usage_mib = 0
        max_cpu_usage = 0

        for stat in self.container.stats(stream=True, decode=True):
            if not self.monitor:
                break
            # in case if container has exited but has not been removed
            self.container.reload()
            if self.container.status == 'exited':
                break
            if 'memory_stats' not in stat or 'usage' not in stat['memory_stats']:
                continue
            # Use the same measure as `docker stats` https://github.com/docker/docker-py/issues/3210
            stats = stat['memory_stats'].get('stats', {})
            inactive_file = stats.get('inactive_file', 0)
            current_mem_usage_bytes = stat['memory_stats']['usage'] - inactive_file
            current_mem_usage_mib = current_mem_usage_bytes / (1024 * 1024)

            if current_mem_usage_mib > max_mem_usage_mib:
                max_mem_usage_mib = current_mem_usage_mib

            # CPU Usage
            current_cpu_percent = self.get_cpu_usage_percent(stat['cpu_stats'], stat['precpu_stats'])
            if current_cpu_percent > max_cpu_usage:
                max_cpu_usage = current_cpu_percent

        if max_mem_usage_mib != 0:
            lgr.info(
                f"RAM usage of the container {self.container.id}: {max_mem_usage_mib}"
            )
        else:
            lgr.warning(
                f"RAM usage of the container {self.container.id} could not be determined."
            )
            max_mem_usage_mib = None

        self.ram_usage = max_mem_usage_mib
        self.cpu_usage = max_cpu_usage
        lgr.info(f"RAM monitor thread for container {self.container.id} has stopped.")

    def start_monitoring(self):
        lgr.info(f"Starting to monitor RAM usage of the container {self.container.id}.")
        self.monitor = True
        self.start()

    def stop_monitoring(self):
        self.monitor = False
        lgr.info("Waiting for RAM monitor thread to finish...")
        self.join()
        name = self.container.name
        print(f'{name} -  CPU: {self.cpu_usage}, Mem: {self.ram_usage}')

    def get_ram_usage(self):
        self.stop_monitoring()
        return self.ram_usage

    def get_cpu_usage(self):
        self.stop_monitoring()
        return self.cpu_usage


if __name__ == '__main__':
     lgr.setLevel(logging.DEBUG)
     logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
     client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
     for container in client.containers.list():
          print(container.stats(stream=False))
          ram_monitor = StatMonitor(container)
          ram_monitor.start_monitoring()
          time.sleep(10)
          ram_monitor.stop_monitoring()



