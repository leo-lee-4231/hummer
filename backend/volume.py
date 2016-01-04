import logging, json
from threading import Thread

import paramiko
from django.conf import settings

from backend.models import Volume
from backend.kubernetes.k8sclient import KubeClient
from backend.utils import get_volume_nfs_dir

logger = logging.getLogger('hummer')


class VolumeBuilder(object):
    """
    ApplicationBuilder is a builder to create an appliction from an image. You
    should offer many necessary arguments.
    """
    volume = None

    def __init__(self, volume):
        self.kubeclient = KubeClient("http://{}:{}{}".format(settings.MASTER_IP,
            settings.K8S_PORT, settings.K8S_API_PATH))

        self.volume = volume
        self.namespace = self.volume.project.user.username
        self.project_name = self.volume.project.name
        self.volume_name = self.project_name + '-' + self.volume.name
        self.capacity = str(self.volume.capacity) + self.volume.capacity_unit
        self.nfs_path = get_volume_nfs_dir(settings.NFS_BASE_DIR,
            self.namespace, self.project_name, self.volume.name)
        self.nfs_server = settings.NFS_IP

    def create_volume(self):
        """
        Create volume by multiple threading.
        """
        creating_thread = Thread(target=self._create_volume)
        creating_thread.start()

    def _create_volume(self):
        """
        First create a persistentvolume, then create a persistentvolumeclaim.
        """
        logger.info('User {} create a volume {} in project {}.'.format(
            self.volume.project.user, self.volume.name,
            self.volume.project.name))

        # create volume dir on nfs server
        if self._create_volume_dir_on_nfs():
            logger.info("Create dir {} on nfs server {} successfully.".format(
                self.nfs_path, self.nfs_server))
        else:
            logger.info("Create dir {} on nfs server {} failed.".format(
                self.nfs_path, self.nfs_server))
            self._update_volume_status(status='error')
            return None

        # create persistentvolume
        if self._create_persistentvolume():
            logger.info("Create persistentvolume {}-{} successfully.".format(
                self.namespace, self.volume_name))
        else:
            logger.info("Create persistentvolume {}-{} failed.".format(
                self.namespace, self.volume_name))
            self._update_volume_status(status='error')
            return None

        # create persistentvolumeclaim
        if self._create_persistentvolumeclaim():
            logger.info("Create persistentvolumeclaim {} successfully.".format(
                self.volume_name))
        else:
            logger.info("Create persistentvolumeclaim {} failed.".format(
                self.volume_name))
            self._update_volume_status(status='error')
            return None

        self._update_volume_status(status='active')

    def _create_volume_dir_on_nfs(self):
        """
        Create direction on nfs server to store volume data.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(self.nfs_server, 22, settings.NFS_USER,
                settings.NFS_PWD)
        except Exception as e:
            logger.debug(e)
            return False
        stdin, stdout, stderr = client.exec_command("mkdir " + self.nfs_path)
        for line in stderr:
            logger.debug(line)
        client.close()
        return True

    def _create_persistentvolume(self):
        return self.kubeclient.create_persistentvolume(
            namespace=self.namespace,
            name=self.volume_name,
            capacity=self.capacity,
            nfs_path=self.nfs_path,
            nfs_server=self.nfs_server
            )

    def _create_persistentvolumeclaim(self):
        return self.kubeclient.create_persistentvolumeclaim(
            namespace=self.namespace,
            name=self.volume_name,
            capacity=self.capacity
            )

    def _update_volume_status(self, status):
        self.volume.status = status
        self.volume.save()


class VolumeDestroyer(object):
    """
    ApplicationDestroyer is to destroy application instance, including controller
    and service.
    """
    pass
