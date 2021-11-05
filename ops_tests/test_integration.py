import pytest
import os
import logging

from pytest_operator.plugin import OpsTest

LOG = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
async def test_deploy_cluster(ops_test: OpsTest):
    units = int(os.getenv("MK8S_CLUSTER_SIZE", 3))
    charm = os.getenv("MK8S_CHARM", "cs:~containers/microk8s")
    constraints = os.getenv("MK8S_CONSTRAINTS", "mem=4G root-disk=20G cores=2")
    charm_channel = os.getenv("MK8S_CHARM_CHANNEL")
    snap_channel = os.getenv("MK8S_SNAP_CHANNEL")
    proxy = os.getenv("MK8S_PROXY")

    if os.getenv("MK8S_KEEP_MODEL"):
        ops_test.keep_model = True

    if charm == "build":
        LOG.info("Build charm")
        charm = await ops_test.build_charm(".")

    if proxy is not None:
        LOG.info("Configure model to use proxy %s", proxy)
        await ops_test.model.set_config(
            {
                "http-proxy": proxy,
                "https-proxy": proxy,
                "ftp-proxy": proxy,
                "no-proxy": "10.0.0.0/8,192.168.0.0/16,127.0.0.0/16",
            }
        )

    charm_config = {}
    if snap_channel:
        charm_config["channel"] = snap_channel
    if proxy:
        charm_config["containerd_env"] = "\n".join(
            [
                "ulimit -n 65536 || true",
                "ulimit -l 16834 || true",
                "HTTP_PROXY={}".format(proxy),
                "HTTPS_PROXY={}".format(proxy),
                "NO_PROXY=10.0.0.0/8,192.168.0.0/16,127.0.0.0/16",
            ]
        )

    LOG.info("Deploy microk8s charm %s with configuration %s", charm, charm_config)
    await ops_test.model.deploy(
        charm,
        num_units=units,
        config=charm_config,
        channel=charm_channel,
        constraints=constraints,
        force=True,
    )

    LOG.info("Wait for MicroK8s cluster")
    await ops_test.model.wait_for_idle(timeout=60 * 60)
